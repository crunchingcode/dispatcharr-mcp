"""Mask credentials in tool results before they reach the model.

Dispatcharr hands back provider credentials in several places: EPG and M3U
URLs carry ``?username=…&password=…`` or ``user:pass@``, Xtream Codes stream
URLs put them in the path (``/live/<user>/<pass>/123.ts``), users carry their
``api_key``, and integration configs hold tokens and auth headers. Log files
repeat the stream URLs. None of that is needed to manage Dispatcharr, and
anything in a tool result may be logged or echoed by the model.

``redact()`` walks a result and masks:
  • values under credential-named keys, at any depth
  • userinfo, credential query parameters and XC path segments in any string

API keys keep their last four characters so a key can still be identified.
Masked values contain ``PLACEHOLDER``, and ``contains_placeholder()`` lets the
server refuse arguments that would write a masked value back.
"""

import re
from typing import Any

PLACEHOLDER = "<redacted>"

# Whole-key or suffix match: `password`, `refresh_token`, `x_api_key`. Not
# `public_key` (not a secret) and not a bare `key` (setting names use it).
_SECRET_KEY = re.compile(
    r"(?:^|_)(?:password|passwd|pass|pwd|secret|token|api_?key|apikey"
    r"|authorization|cookie|private_key|access_key)$",
    re.IGNORECASE,
)
_API_KEY = re.compile(r"(?:^|_)api_?key$|^apikey$", re.IGNORECASE)

# scheme://user:pass@host → scheme://<redacted>:<redacted>@host
_USERINFO = re.compile(r"(\b[a-z][a-z0-9+.-]*://)[^/\s@\"']+@", re.IGNORECASE)
# ?username=… &password=… ;token=…
_QUERY = re.compile(
    r"([?&;](?:username|user|password|pass|pwd|passwd|token|access_token"
    r"|api_?key|apikey|key|auth|secret)=)[^&#\s\"']*",
    re.IGNORECASE,
)
# XC paths: /live|movie|series|timeshift/<user>/<pass>/…
_XC_PREFIXED = re.compile(
    r"(https?://[^/\s\"']+(?:/[^/\s\"']+)*?/(?:live|movie|series|timeshift)/)"
    r"[^/\s\"']+/[^/\s\"']+/",
    re.IGNORECASE,
)
# Bare XC: host/<user>/<pass>/<stream id>, as used in M3U playlists. Only a
# bare id or a stream extension, so a logo like host/media/logos/123.png
# isn't mistaken for one.
_XC_BARE = re.compile(
    r"(https?://[^/\s\"']+/)[^/\s\"']+/[^/\s\"']+/(\d+(?:\.(?:ts|m3u8))?)(?=$|[\s\"'?#])",
    re.IGNORECASE,
)


def redact_text(text: str) -> str:
    """Mask credentials inside URLs anywhere in `text`."""
    text = _USERINFO.sub(rf"\1{PLACEHOLDER}:{PLACEHOLDER}@", text)
    text = _QUERY.sub(rf"\1{PLACEHOLDER}", text)
    text = _XC_PREFIXED.sub(rf"\1{PLACEHOLDER}/{PLACEHOLDER}/", text)
    text = _XC_BARE.sub(rf"\1{PLACEHOLDER}/{PLACEHOLDER}/\2", text)
    return text


def _mask_value(key: str, value: Any, api_keys: frozenset[str]) -> Any:
    """Mask the value under a credential-named key."""
    if isinstance(value, dict | list):
        return redact(value, api_keys)
    # Unset and flag values say nothing secret, and keeping them shows the
    # model whether a credential is configured.
    if value is None or isinstance(value, bool) or value == "":
        return value
    if isinstance(value, str) and (_API_KEY.search(key) or key in api_keys):
        return PLACEHOLDER + (value[-4:] if len(value) > 8 else "")
    return PLACEHOLDER


def redact(obj: Any, api_keys: frozenset[str] = frozenset()) -> Any:
    """Return a copy of `obj` with credentials masked.

    `api_keys` names extra keys holding API keys (e.g. ``key`` in the API-key
    listing); like ``api_key`` they keep their last four characters.
    """
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, list):
        return [redact(v, api_keys) for v in obj]
    if isinstance(obj, dict):
        # Settings are {"key": <name>, "value": ...}: the name says what the value is.
        name = obj.get("key")
        if isinstance(name, str) and _SECRET_KEY.search(name) and "value" in obj:
            obj = {**obj, "value": _mask_value(name, obj["value"], api_keys)}
        return {
            k: _mask_value(k, v, api_keys)
            if isinstance(k, str) and (_SECRET_KEY.search(k) or k in api_keys)
            else redact(v, api_keys)
            for k, v in obj.items()
        }
    return obj


def contains_placeholder(obj: Any) -> bool:
    """True if `obj` holds a masked value anywhere."""
    if isinstance(obj, str):
        return PLACEHOLDER in obj
    if isinstance(obj, list | tuple):
        return any(contains_placeholder(v) for v in obj)
    if isinstance(obj, dict):
        return any(contains_placeholder(v) for v in obj.values())
    return False

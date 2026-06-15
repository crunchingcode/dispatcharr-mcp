"""Dispatcharr MCP server — exposes Dispatcharr IPTV management to AI agents.

Tools are grouped by domain:
  • Accounts/Users  — users, groups, permissions, API keys
  • Channels        — list, get, create, update, delete channels & groups
  • Channel Logos   — logo entries for channels (create/update/delete/cleanup)
  • Streams         — list/get raw M3U streams by source
  • Proxy           — live stream status and control (change, stop, failover)
  • EPG             — EPG sources and programme data
  • M3U Accounts    — manage M3U provider accounts, filters, profiles, server-groups
  • VOD             — movies, series, episodes, unified list, provider metadata
  • VOD Logos       — artwork logos for VOD content (create/update/delete/cleanup)
  • System          — settings, stream profiles, useragents, system events
  • Notifications   — system notifications
  • Connect         — integrations, subscriptions, delivery logs
  • DVR             — recordings, series rules, recurring rules
  • Plugins         — installed plugins and plugin repositories
"""

from mcp.server.fastmcp import FastMCP

from dispatcharr_mcp.client import DispatcharrClient

mcp = FastMCP("Dispatcharr")


def _client() -> DispatcharrClient:
    """Instantiate per-call so the MCP server process doesn't hold a login
    session open indefinitely — the client re-uses its JWT until it expires."""
    return DispatcharrClient()


def _clean(params: dict) -> dict:
    """Omit unset parameters so the API applies its own defaults rather than
    receiving explicit nulls that could override or invalidate fields."""
    return {k: v for k, v in params.items() if v is not None}


# ---------------------------------------------------------------------------
# CHANNELS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_channels(
    search: str | None = None,
    channel_group: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List channels with optional filtering.

    Returns a paginated list of channels. Use `search` to filter by name,
    `channel_group` to filter by group name, and `page`/`page_size` for pagination.
    """
    return await _client().get(
        "/api/channels/channels/",
        params=_clean(
            {
                "search": search,
                "channel_group": channel_group,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def get_channel(channel_id: int) -> dict:
    """Get a single channel by its integer ID."""
    return await _client().get(f"/api/channels/channels/{channel_id}/")


@mcp.tool()
async def create_channel(
    name: str,
    channel_number: float | None = None,
    channel_group_id: int | None = None,
) -> dict:
    """Create a new channel.

    Provide at minimum a `name`. Optionally assign a channel number and group.
    """
    data: dict = {"name": name}
    if channel_number is not None:
        data["channel_number"] = channel_number
    if channel_group_id is not None:
        data["channel_group"] = channel_group_id
    return await _client().post("/api/channels/channels/", data=data)


@mcp.tool()
async def update_channel(channel_id: int, fields: dict) -> dict:
    """Partially update a channel.

    Pass any subset of channel fields as `fields` (e.g. {"name": "BBC One",
    "channel_number": 1.0}).  Only provided fields are changed.
    """
    return await _client().patch(f"/api/channels/channels/{channel_id}/", data=fields)


@mcp.tool()
async def delete_channel(channel_id: int) -> dict:
    """Delete a channel by ID."""
    return await _client().delete(f"/api/channels/channels/{channel_id}/")


@mcp.tool()
async def get_channel_streams(channel_id: int) -> dict:
    """Get all streams (M3U sources) assigned to a specific channel."""
    return await _client().get(f"/api/channels/channels/{channel_id}/streams/")


@mcp.tool()
async def get_channel_stream_stats(
    channel_id: int,
    ids: list[int] | None = None,
    since: str | None = None,
) -> dict:
    """Return a minimal stats delta for streams attached to a channel.

    Used to poll live stream health without fetching full stream objects.
    `ids` filters to specific stream IDs; `since` is an ISO-8601 timestamp
    for incremental updates.
    """
    return await _client().get(
        f"/api/channels/channels/{channel_id}/streams/stats/",
        params=_clean({"ids": ids, "since": since}),
    )


@mcp.tool()
async def get_channels_in_number_range(
    start: int,
    end: int | None = None,
) -> dict:
    """Get channels occupying channel numbers in a range.

    `start` is required. `end` defaults to `start` if omitted (single number lookup).
    Includes channels whose effective number is set via an override.
    """
    return await _client().get(
        "/api/channels/channels/numbers-in-range/",
        params=_clean({"start": start, "end": end}),
    )


# ---------------------------------------------------------------------------
# CHANNEL GROUPS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_channel_groups() -> list:
    """List all channel groups."""
    return await _client().get("/api/channels/groups/")


@mcp.tool()
async def create_channel_group(name: str) -> dict:
    """Create a new channel group."""
    return await _client().post("/api/channels/groups/", data={"name": name})


@mcp.tool()
async def delete_channel_group(group_id: int) -> dict:
    """Delete a channel group by ID."""
    return await _client().delete(f"/api/channels/groups/{group_id}/")


# ---------------------------------------------------------------------------
# STREAMS (raw M3U streams from provider accounts)
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_streams(
    search: str | None = None,
    m3u_account: int | None = None,
    channel_group_name: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List raw M3U streams from provider accounts.

    These are the source streams imported from M3U playlists, not the
    channel output. Filter by `m3u_account` (account ID), group name,
    or free-text `search`.
    """
    return await _client().get(
        "/api/channels/streams/",
        params=_clean(
            {
                "search": search,
                "m3u_account": m3u_account,
                "channel_group_name": channel_group_name,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def get_stream(stream_id: int) -> dict:
    """Get a single M3U stream by its integer ID."""
    return await _client().get(f"/api/channels/streams/{stream_id}/")


@mcp.tool()
async def create_channel_from_stream(
    stream_id: int,
    name: str | None = None,
    channel_number: float | None = None,
    channel_profile_ids: list[int] | None = None,
) -> dict:
    """Create a channel directly from an existing stream.

    This is the quick way to add a channel: provide the `stream_id` and
    Dispatcharr will create a matching channel and link the stream.
    Optionally supply a custom `name`, `channel_number`, and which
    `channel_profile_ids` the new channel should belong to (omit for all profiles).
    """
    data: dict = {"stream_id": stream_id}
    if name is not None:
        data["name"] = name
    if channel_number is not None:
        data["channel_number"] = channel_number
    if channel_profile_ids is not None:
        data["channel_profile_ids"] = channel_profile_ids
    return await _client().post("/api/channels/channels/from-stream/", data=data)


@mcp.tool()
async def preview_regex_streams(
    channel_group: str,
    find: str | None = None,
    match: str | None = None,
    replace: str | None = None,
    exclude: str | None = None,
    limit: int | None = None,
) -> dict:
    """Preview regex find/replace results for streams in a channel group.

    Shows what names would be produced before committing a bulk regex rename.
    `channel_group` is required. `find` and `replace` define the substitution;
    `match` filters which stream names are affected; `exclude` skips matching
    names; `limit` caps the number of results returned.
    """
    return await _client().get(
        "/api/channels/streams/regex-preview/",
        params=_clean({
            "channel_group": channel_group,
            "find": find,
            "match": match,
            "replace": replace,
            "exclude": exclude,
            "limit": limit,
        }),
    )


# ---------------------------------------------------------------------------
# PROXY — live stream status and control
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_proxy_status() -> dict:
    """Get live status of all currently active proxy streams.

    Returns client counts, current stream URLs, buffer stats, and more for
    every channel that is actively streaming right now.
    """
    return await _client().get("/proxy/ts/status")


@mcp.tool()
async def get_channel_proxy_status(channel_id: str) -> dict:
    """Get the live proxy status for a specific channel.

    `channel_id` is the channel's string identifier used by the proxy
    (typically the channel number or UUID).
    """
    return await _client().get(f"/proxy/ts/status/{channel_id}")


@mcp.tool()
async def change_channel_stream(channel_id: str) -> dict:
    """Force a channel to switch to its next available stream source.

    Use this when a stream is buffering badly or has failed—Dispatcharr
    will immediately try the next source in the failover list.
    """
    return await _client().post(f"/proxy/ts/change_stream/{channel_id}")


@mcp.tool()
async def next_channel_stream(channel_id: str) -> dict:
    """Advance a channel to the next stream in its rotation.

    Similar to `change_channel_stream` but explicitly moves forward one
    position in the stream list rather than picking the best available.
    """
    return await _client().post(f"/proxy/ts/next_stream/{channel_id}")


@mcp.tool()
async def stop_channel_stream(channel_id: str) -> dict:
    """Stop all active streams for a channel, disconnecting all clients."""
    return await _client().post(f"/proxy/ts/stop/{channel_id}")


@mcp.tool()
async def stop_channel_client(channel_id: str) -> dict:
    """Stop a specific client connection on a channel without stopping others."""
    return await _client().post(f"/proxy/ts/stop_client/{channel_id}")


# ---------------------------------------------------------------------------
# EPG
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_epg_sources() -> list:
    """List all configured EPG (Electronic Programme Guide) sources."""
    return await _client().get("/api/epg/sources/")


@mcp.tool()
async def get_epg_source(source_id: int) -> dict:
    """Get a single EPG source by ID."""
    return await _client().get(f"/api/epg/sources/{source_id}/")


@mcp.tool()
async def create_epg_source(
    name: str,
    source_type: str = "xmltv",
    url: str | None = None,
    is_active: bool = True,
    refresh_interval: int | None = None,
    priority: int | None = None,
) -> dict:
    """Create a new EPG source.

    `source_type` must be one of: ``xmltv`` (default), ``schedules_direct``,
    or ``dummy``.  For XMLTV sources supply the `url` pointing to an .xml or
    .xml.gz EPG feed.
    """
    data: dict = {"name": name, "source_type": source_type, "is_active": is_active}
    if url is not None:
        data["url"] = url
    if refresh_interval is not None:
        data["refresh_interval"] = refresh_interval
    if priority is not None:
        data["priority"] = priority
    return await _client().post("/api/epg/sources/", data=data)


@mcp.tool()
async def update_epg_source(source_id: int, fields: dict) -> dict:
    """Partially update an EPG source.

    Pass any subset of EPG source fields as `fields`
    (e.g. ``{"url": "https://...", "is_active": True}``).
    """
    return await _client().patch(f"/api/epg/sources/{source_id}/", data=fields)


@mcp.tool()
async def delete_epg_source(source_id: int) -> dict:
    """Delete an EPG source by ID."""
    return await _client().delete(f"/api/epg/sources/{source_id}/")


# ---------------------------------------------------------------------------
# Schedules Direct lineup management (EPG sources with source_type=schedules_direct)
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_sd_lineups(source_id: int) -> dict:
    """List the Schedules Direct lineups active on an EPG source.

    `source_id` must be the ID of a Schedules Direct EPG source.

    Returns the active lineups plus ``changes_remaining`` (SD limits 6
    lineup additions per 24-hour period, resetting at midnight UTC) and
    ``changes_reset_at`` (when the counter resets, if a lockout is in effect).
    """
    return await _client().get(f"/api/epg/sources/{source_id}/sd-lineups/")


@mcp.tool()
async def add_sd_lineup(source_id: int, lineup: str) -> dict:
    """Add a Schedules Direct lineup to an EPG source.

    `source_id` must be the ID of a Schedules Direct EPG source.
    `lineup` is the SD lineup identifier, e.g. ``"USA-NJ29486-X"``.
    Use `search_sd_lineups` to find available lineup IDs for a postal code.

    SD allows a maximum of 4 active lineups and 6 lineup additions per
    24-hour period.  The response includes ``changes_remaining`` so you can
    track headroom before the daily limit is reached.
    """
    return await _client().post(
        f"/api/epg/sources/{source_id}/sd-lineups/",
        data={"lineup": lineup},
    )


@mcp.tool()
async def remove_sd_lineup(source_id: int, lineup: str) -> dict:
    """Remove a Schedules Direct lineup from an EPG source.

    `source_id` must be the ID of a Schedules Direct EPG source.
    `lineup` is the SD lineup identifier, e.g. ``"USA-NJ29486-X"``.
    """
    return await _client().delete_with_body(
        f"/api/epg/sources/{source_id}/sd-lineups/",
        data={"lineup": lineup},
    )


@mcp.tool()
async def search_sd_lineups(source_id: int, country: str, postalcode: str) -> dict:
    """Search available Schedules Direct lineups by country and postal code.

    `source_id` must be the ID of a Schedules Direct EPG source — its
    credentials are used to authenticate with Schedules Direct on your behalf.
    `country` is the ISO 3166-1 alpha-3 country code, e.g. ``"USA"`` or ``"CAN"``.
    `postalcode` is the ZIP or postal code, e.g. ``"07030"``.

    Returns a flat list of available lineups, each with ``lineup`` (the ID to
    pass to `add_sd_lineup`), ``name``, ``transport``, ``location``, and ``headend``.
    """
    return await _client().post(
        f"/api/epg/sources/{source_id}/sd-lineups/search/",
        data={"country": country, "postalcode": postalcode},
    )


@mcp.tool()
async def get_epg_program_poster_url(program_id: int) -> dict:
    """Get the poster image URL for a Schedules Direct EPG program.

    Returns the URL of the Dispatcharr poster proxy endpoint for the given
    program.  The proxy is publicly accessible (no auth required) and is
    cached by nginx for 24 hours.

    Only works for programs from Schedules Direct EPG sources that have
    poster artwork stored; others return 404 from the proxy.
    """
    client = _client()
    url = f"{client._base}/api/epg/programs/{program_id}/poster/"
    return {"poster_url": url, "program_id": program_id}


@mcp.tool()
async def upload_epg_source(
    name: str,
    source_type: str = "xmltv",
    url: str | None = None,
    file_path: str | None = None,
    is_active: bool = True,
    refresh_interval: int | None = None,
    priority: int | None = None,
    api_key: str | None = None,
) -> dict:
    """Create an EPG source via the upload endpoint.

    Functionally equivalent to `create_epg_source` but posts to
    ``/api/epg/sources/upload/``.  Use this when you want to register a
    source by its server-side `file_path` (a path already accessible on
    the Dispatcharr host) rather than a remote URL.

    `source_type` must be one of: ``xmltv`` (default), ``schedules_direct``,
    or ``dummy``.
    """
    data: dict = {"name": name, "source_type": source_type, "is_active": is_active}
    if url is not None:
        data["url"] = url
    if file_path is not None:
        data["file_path"] = file_path
    if api_key is not None:
        data["api_key"] = api_key
    if refresh_interval is not None:
        data["refresh_interval"] = refresh_interval
    if priority is not None:
        data["priority"] = priority
    return await _client().post("/api/epg/sources/upload/", data=data)


@mcp.tool()
async def list_epg_data(page: int | None = None, page_size: int | None = None) -> dict:
    """List EPG data entries (programme metadata from EPG sources)."""
    return await _client().get(
        "/api/epg/epgdata/",
        params=_clean({"page": page, "page_size": page_size}),
    )


@mcp.tool()
async def list_epg_programs(
    page: int | None = None, page_size: int | None = None
) -> dict:
    """List EPG program schedule entries (start/stop times, titles, descriptions)."""
    return await _client().get(
        "/api/epg/programs/",
        params=_clean({"page": page, "page_size": page_size}),
    )


@mcp.tool()
async def search_epg_programs(
    title: str | None = None,
    title_regex: str | None = None,
    title_whole_words: bool | None = None,
    description: str | None = None,
    description_regex: str | None = None,
    description_whole_words: bool | None = None,
    channel: str | None = None,
    channel_id: int | None = None,
    tvg_id: str | None = None,
    epg_source: int | None = None,
    group: str | None = None,
    stream: int | None = None,
    airing_at: str | None = None,
    start_after: str | None = None,
    start_before: str | None = None,
    end_after: str | None = None,
    end_before: str | None = None,
    fields: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """Search EPG programme entries with rich filters.

    All filters are optional and combinable:
    - `title` / `title_regex` — match programme titles (regex enables `title_whole_words`)
    - `description` / `description_regex` — match descriptions
    - `channel` — channel name substring; `channel_id` — integer channel ID
    - `tvg_id` — EPG TVG-ID; `epg_source` — EPG source ID
    - `group` — channel group name; `stream` — stream ID
    - `airing_at` — ISO-8601 datetime (programme must be airing at that instant)
    - `start_after` / `start_before` / `end_after` / `end_before` — time window filters
    - `fields` — comma-separated list of fields to include in the response
    """
    return await _client().get(
        "/api/epg/programs/search/",
        params=_clean({
            "title": title,
            "title_regex": title_regex,
            "title_whole_words": title_whole_words,
            "description": description,
            "description_regex": description_regex,
            "description_whole_words": description_whole_words,
            "channel": channel,
            "channel_id": channel_id,
            "tvg_id": tvg_id,
            "epg_source": epg_source,
            "group": group,
            "stream": stream,
            "airing_at": airing_at,
            "start_after": start_after,
            "start_before": start_before,
            "end_after": end_after,
            "end_before": end_before,
            "fields": fields,
            "page": page,
            "page_size": page_size,
        }),
    )


# ---------------------------------------------------------------------------
# M3U ACCOUNTS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_m3u_accounts() -> list:
    """List all configured M3U provider accounts."""
    return await _client().get("/api/m3u/accounts/")


@mcp.tool()
async def get_m3u_account(account_id: int) -> dict:
    """Get details for a specific M3U account by ID."""
    return await _client().get(f"/api/m3u/accounts/{account_id}/")


@mcp.tool()
async def create_m3u_account(
    name: str,
    server_url: str | None = None,
    max_streams: int = 0,
    is_active: bool = True,
    account_type: str = "STD",
    username: str | None = None,
    password: str | None = None,
    refresh_interval: int | None = None,
) -> dict:
    """Create a new M3U provider account.

    `account_type` is ``STD`` (standard M3U URL, the default) or ``XC``
    (Xtream Codes).  For a standard M3U simply pass `server_url`.  Set
    `max_streams` to ``0`` for unlimited concurrent streams.
    """
    data: dict = {
        "name": name,
        "is_active": is_active,
        "account_type": account_type,
        "max_streams": max_streams,
    }
    if server_url is not None:
        data["server_url"] = server_url
    if username is not None:
        data["username"] = username
    if password is not None:
        data["password"] = password
    if refresh_interval is not None:
        data["refresh_interval"] = refresh_interval
    return await _client().post("/api/m3u/accounts/", data=data)


@mcp.tool()
async def update_m3u_account(account_id: int, fields: dict) -> dict:
    """Partially update an M3U account.

    Pass any subset of M3U account fields as `fields`
    (e.g. ``{"name": "New Name", "is_active": False}``).
    """
    return await _client().patch(f"/api/m3u/accounts/{account_id}/", data=fields)


@mcp.tool()
async def delete_m3u_account(account_id: int) -> dict:
    """Delete an M3U account by ID."""
    return await _client().delete(f"/api/m3u/accounts/{account_id}/")


@mcp.tool()
async def refresh_m3u_account(account_id: int) -> dict:
    """Trigger an immediate refresh/re-import of an M3U account's streams."""
    return await _client().post(f"/api/m3u/refresh/{account_id}/")


@mcp.tool()
async def list_m3u_filters(account_id: int) -> list:
    """List stream filters configured for a specific M3U account."""
    return await _client().get(f"/api/m3u/accounts/{account_id}/filters/")


# ---------------------------------------------------------------------------
# CHANNEL PROFILES
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_channel_profiles() -> list:
    """List all channel profiles (output profiles used for different clients)."""
    return await _client().get("/api/channels/profiles/")


# ---------------------------------------------------------------------------
# VOD — Video on Demand
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_movies(
    search: str | None = None,
    category: str | None = None,
    year: int | None = None,
    m3u_account: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List VOD movies with optional filtering.

    Filter by title `search`, `category`, release `year`, or `m3u_account` ID.
    """
    return await _client().get(
        "/api/vod/movies/",
        params=_clean(
            {
                "search": search,
                "category": category,
                "year": year,
                "m3u_account": m3u_account,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def get_movie(movie_id: int) -> dict:
    """Get details for a specific movie by ID."""
    return await _client().get(f"/api/vod/movies/{movie_id}/")


@mcp.tool()
async def list_series(
    search: str | None = None,
    category: str | None = None,
    year: int | None = None,
    m3u_account: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List VOD TV series with optional filtering."""
    return await _client().get(
        "/api/vod/series/",
        params=_clean(
            {
                "search": search,
                "category": category,
                "year": year,
                "m3u_account": m3u_account,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def get_series(series_id: int) -> dict:
    """Get details for a specific TV series by ID."""
    return await _client().get(f"/api/vod/series/{series_id}/")


@mcp.tool()
async def list_episodes(
    series_id: int | None = None,
    season_number: int | None = None,
    search: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List VOD episodes, optionally filtered by series and/or season."""
    return await _client().get(
        "/api/vod/episodes/",
        params=_clean(
            {
                "series": series_id,
                "season_number": season_number,
                "search": search,
                "page": page,
                "page_size": page_size,
            }
        ),
    )


@mcp.tool()
async def list_vod_categories(
    category_type: str | None = None,
    m3u_account: int | None = None,
) -> list:
    """List VOD categories.

    Use `category_type` to filter: "movie" or "series".
    """
    return await _client().get(
        "/api/vod/categories/",
        params=_clean({"category_type": category_type, "m3u_account": m3u_account}),
    )


# ---------------------------------------------------------------------------
# SYSTEM
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_core_settings() -> list:
    """Get Dispatcharr core settings (server configuration, defaults, etc.)."""
    return await _client().get("/api/core/settings/")


@mcp.tool()
async def list_stream_profiles() -> list:
    """List stream profiles (FFmpeg/Streamlink/VLC output configurations)."""
    return await _client().get("/api/core/streamprofiles/")


@mcp.tool()
async def get_system_events(
    limit: int | None = None,
    offset: int | None = None,
    event_type: str | None = None,
) -> dict:
    """Get recent system events (channel starts, stops, buffering, client connections).

    Use `limit` (default 100, max 1000), `offset` for pagination, and
    `event_type` to filter by a specific event kind.
    """
    return await _client().get(
        "/api/core/system-events/",
        params=_clean({"limit": limit, "offset": offset, "event_type": event_type}),
    )


@mcp.tool()
async def list_stream_delivery_logs(
    page: int | None = None, page_size: int | None = None
) -> dict:
    """List stream delivery/webhook logs from the Connect integrations system."""
    return await _client().get(
        "/api/connect/logs/",
        params=_clean({"page": page, "page_size": page_size}),
    )


@mcp.tool()
async def list_integrations() -> list:
    """List all configured Connect integrations (webhooks, API callbacks, scripts)."""
    return await _client().get("/api/connect/integrations/")


@mcp.tool()
async def update_channel_group(group_id: int, name: str) -> dict:
    """Rename a channel group.

    Note: groups that have M3U account associations cannot be renamed —
    the API will return an error in that case.
    """
    return await _client().patch(f"/api/channels/groups/{group_id}/", data={"name": name})


# ---------------------------------------------------------------------------
# EPG — current programmes and TV grid
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_current_programs(channel_uuids: list[str] | None = None) -> list:
    """Get the currently-playing programme for channels.

    Pass a list of channel UUIDs to filter to specific channels, or omit
    `channel_uuids` (or pass null) to fetch the now-playing programme for
    every channel that has EPG data.
    """
    return await _client().post(
        "/api/epg/current-programs/",
        data={"channel_uuids": channel_uuids},
    )


@mcp.tool()
async def get_epg_grid() -> list:
    """Get the full EPG grid — past hour, now, and next 24 hours.

    Returns programme data across all channels, suitable for building a
    TV guide view or answering "what's on tonight" style queries.
    """
    return await _client().get("/api/epg/grid/")


# ---------------------------------------------------------------------------
# SYSTEM — version
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_version() -> dict:
    """Get the running Dispatcharr application version."""
    return await _client().get("/api/core/version/")


# ---------------------------------------------------------------------------
# DVR — schedule, manage and control recordings
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_recordings() -> list:
    """List all DVR recordings."""
    return await _client().get("/api/channels/recordings/")


@mcp.tool()
async def get_recording(recording_id: int) -> dict:
    """Get details for a specific DVR recording by ID."""
    return await _client().get(f"/api/channels/recordings/{recording_id}/")


@mcp.tool()
async def schedule_recording(
    channel_id: int,
    start_time: str,
    end_time: str,
) -> dict:
    """Schedule a new DVR recording.

    `channel_id` is the integer channel ID.
    `start_time` and `end_time` must be ISO 8601 datetime strings
    (e.g. ``"2026-04-22T20:00:00Z"``).
    """
    return await _client().post(
        "/api/channels/recordings/",
        data={"channel": channel_id, "start_time": start_time, "end_time": end_time},
    )


@mcp.tool()
async def delete_recording(recording_id: int) -> dict:
    """Delete a DVR recording by ID.

    Also stops any active recording stream and removes the file from disk.
    """
    return await _client().delete(f"/api/channels/recordings/{recording_id}/")


@mcp.tool()
async def stop_recording(recording_id: int) -> dict:
    """Stop an in-progress recording early.

    Retains the partial file so it can still be played back. Use
    `delete_recording` if you want to remove it entirely.
    """
    return await _client().post(f"/api/channels/recordings/{recording_id}/stop/", data={})


@mcp.tool()
async def extend_recording(recording_id: int, extra_minutes: int) -> dict:
    """Extend an in-progress recording by additional minutes.

    The running stream is not interrupted — the deadline is adjusted
    dynamically. `extra_minutes` must be a positive integer.
    """
    return await _client().post(
        f"/api/channels/recordings/{recording_id}/extend/",
        data={"extra_minutes": extra_minutes},
    )


# ---------------------------------------------------------------------------
# DVR — series recording rules
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_series_rules() -> dict:
    """List all configured DVR series recording rules."""
    return await _client().get("/api/channels/series-rules/")


@mcp.tool()
async def create_series_rule(
    tvg_id: str,
    mode: str = "all",
    title: str | None = None,
) -> dict:
    """Create (or update) a DVR series recording rule.

    `tvg_id` is the EPG channel TVG-ID to record.
    `mode` is either ``"all"`` (record every episode) or ``"new"``
    (only episodes not yet recorded).
    `title` narrows the rule to a specific series title on that channel.
    Rules are evaluated immediately after creation.
    """
    return await _client().post(
        "/api/channels/series-rules/",
        data=_clean({"tvg_id": tvg_id, "mode": mode, "title": title}),
    )


@mcp.tool()
async def delete_series_rule(tvg_id: str) -> dict:
    """Delete a DVR series rule by TVG-ID.

    Future scheduled recordings for the rule are also removed; already
    completed recordings are kept.
    """
    return await _client().delete(f"/api/channels/series-rules/{tvg_id}/")


@mcp.tool()
async def evaluate_series_rules(tvg_id: str | None = None) -> dict:
    """Evaluate series recording rules and schedule matching episodes.

    Pass a `tvg_id` to evaluate only rules for that channel, or omit it
    to evaluate all rules.
    """
    return await _client().post(
        "/api/channels/series-rules/evaluate/",
        data=_clean({"tvg_id": tvg_id}),
    )


@mcp.tool()
async def preview_series_rule(
    tvg_id: str | None = None,
    title: str | None = None,
    title_mode: str = "exact",
    description: str | None = None,
    description_mode: str = "contains",
    mode: str = "all",
    limit: int | None = None,
) -> dict:
    """Preview which EPG programmes a series rule would match before saving it.

    `tvg_id` scopes the search to a specific EPG channel; omit to search all
    channels. `title_mode` is one of ``exact``, ``contains``, or ``regex``.
    `description_mode` is one of ``contains`` or ``regex``.
    `mode` is ``all`` or ``new``. `limit` caps results (default 25, max 100).
    """
    return await _client().post(
        "/api/channels/series-rules/preview/",
        data=_clean({
            "tvg_id": tvg_id,
            "title": title,
            "title_mode": title_mode,
            "description": description,
            "description_mode": description_mode,
            "mode": mode,
            "limit": limit,
        }),
    )


# ---------------------------------------------------------------------------
# DVR — recurring recording rules (time-based)
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_recurring_rules() -> list:
    """List all recurring DVR recording rules."""
    return await _client().get("/api/channels/recurring-rules/")


@mcp.tool()
async def create_recurring_rule(
    channel_id: int,
    name: str,
    start_time: str,
    end_time: str,
    days_of_week: list[int] | None = None,
    enabled: bool = True,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Create a recurring DVR recording rule.

    `start_time` / `end_time` are wall-clock times in ``"HH:MM:SS"`` format.
    `days_of_week` is a list of integers where 0 = Monday … 6 = Sunday.
    `start_date` / `end_date` are optional ISO date strings (``"YYYY-MM-DD"``)
    that bound when the rule is active.
    """
    data: dict = {
        "channel": channel_id,
        "name": name,
        "start_time": start_time,
        "end_time": end_time,
        "enabled": enabled,
    }
    if days_of_week is not None:
        data["days_of_week"] = days_of_week
    if start_date is not None:
        data["start_date"] = start_date
    if end_date is not None:
        data["end_date"] = end_date
    return await _client().post("/api/channels/recurring-rules/", data=data)


@mcp.tool()
async def update_recurring_rule(rule_id: int, fields: dict) -> dict:
    """Partially update a recurring recording rule.

    Pass any subset of rule fields as `fields`
    (e.g. ``{"enabled": False}`` or ``{"end_time": "22:30:00"}``).
    """
    return await _client().patch(f"/api/channels/recurring-rules/{rule_id}/", data=fields)


@mcp.tool()
async def delete_recurring_rule(rule_id: int) -> dict:
    """Delete a recurring recording rule by ID."""
    return await _client().delete(f"/api/channels/recurring-rules/{rule_id}/")


# ---------------------------------------------------------------------------
# M3U FILTERS — fine-grained stream filtering per account
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_m3u_filter(
    account_id: int,
    regex_pattern: str,
    filter_type: str = "group",
    exclude: bool = False,
    order: int | None = None,
) -> dict:
    """Create a stream filter for an M3U account.

    `filter_type` is one of ``"group"`` (match by group title),
    ``"name"`` (match by stream name), or ``"url"`` (match by stream URL).
    `regex_pattern` is a regex applied to the chosen field.
    If `exclude` is ``True``, matching streams are excluded; if ``False``
    (default), only matching streams are included.
    """
    return await _client().post(
        f"/api/m3u/accounts/{account_id}/filters/",
        data=_clean(
            {
                "filter_type": filter_type,
                "regex_pattern": regex_pattern,
                "exclude": exclude,
                "order": order,
            }
        ),
    )


@mcp.tool()
async def update_m3u_filter(account_id: int, filter_id: int, fields: dict) -> dict:
    """Partially update an M3U stream filter.

    Pass any subset of filter fields as `fields`
    (e.g. ``{"regex_pattern": "HD$", "exclude": True}``).
    """
    return await _client().patch(
        f"/api/m3u/accounts/{account_id}/filters/{filter_id}/", data=fields
    )


@mcp.tool()
async def delete_m3u_filter(account_id: int, filter_id: int) -> dict:
    """Delete an M3U stream filter by account ID and filter ID."""
    return await _client().delete(f"/api/m3u/accounts/{account_id}/filters/{filter_id}/")


# ---------------------------------------------------------------------------
# CHANNEL PROFILES — create / delete
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_channel_profile(name: str) -> dict:
    """Create a new channel profile.

    Channel profiles define different output sets for different client
    types (e.g. a 4K profile, a mobile profile, etc.).
    """
    return await _client().post("/api/channels/profiles/", data={"name": name})


@mcp.tool()
async def delete_channel_profile(profile_id: int) -> dict:
    """Delete a channel profile by ID."""
    return await _client().delete(f"/api/channels/profiles/{profile_id}/")


# ---------------------------------------------------------------------------
# HDHR (HDHomeRun emulation)
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_hdhr_devices() -> list:
    """List all configured HDHomeRun virtual tuner devices."""
    return await _client().get("/api/hdhr/devices/")


@mcp.tool()
async def get_hdhr_device(device_id: int) -> dict:
    """Get a single HDHomeRun virtual tuner device by ID."""
    return await _client().get(f"/api/hdhr/devices/{device_id}/")


@mcp.tool()
async def create_hdhr_device(
    device_id: str,
    friendly_name: str | None = None,
    tuner_count: int | None = None,
) -> dict:
    """Create a new HDHomeRun virtual tuner device.

    `device_id` is the unique device identifier string (required).
    `friendly_name` is an optional human-readable label.
    `tuner_count` sets the number of virtual tuners (defaults to the
    Dispatcharr server default if omitted).
    """
    data: dict = {"device_id": device_id}
    if friendly_name is not None:
        data["friendly_name"] = friendly_name
    if tuner_count is not None:
        data["tuner_count"] = tuner_count
    return await _client().post("/api/hdhr/devices/", data=data)


@mcp.tool()
async def update_hdhr_device(device_id: int, fields: dict) -> dict:
    """Partially update an HDHomeRun virtual tuner device.

    Pass any subset of device fields as `fields`
    (e.g. ``{"friendly_name": "Living Room", "tuner_count": 4}``).
    """
    return await _client().patch(f"/api/hdhr/devices/{device_id}/", data=fields)


@mcp.tool()
async def delete_hdhr_device(device_id: int) -> dict:
    """Delete an HDHomeRun virtual tuner device by ID."""
    return await _client().delete(f"/api/hdhr/devices/{device_id}/")


# ---------------------------------------------------------------------------
# CHANNEL LOGOS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_channel_logos(
    search: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List channel logo entries stored in Dispatcharr.

    Logos can be referenced by channels to display artwork in EPG clients.
    Use `search` to filter by name, and `page`/`page_size` for pagination.
    """
    return await _client().get(
        "/api/channels/logos/",
        params=_clean({"search": search, "page": page, "page_size": page_size}),
    )


@mcp.tool()
async def get_channel_logo(logo_id: int) -> dict:
    """Get a single channel logo entry by ID."""
    return await _client().get(f"/api/channels/logos/{logo_id}/")


@mcp.tool()
async def create_channel_logo(name: str, url: str) -> dict:
    """Create a channel logo entry from a remote URL.

    `name` is a human-readable label.
    `url` is the public HTTP(S) URL of the logo image.
    Dispatcharr will cache the image server-side.

    Note: to upload a local file instead, use the Dispatcharr web UI —
    the file-upload endpoint requires multipart support not yet available
    in this MCP server.
    """
    return await _client().post("/api/channels/logos/", data={"name": name, "url": url})


@mcp.tool()
async def update_channel_logo(logo_id: int, fields: dict) -> dict:
    """Partially update a channel logo entry.

    Pass any subset of logo fields as `fields`
    (e.g. ``{"name": "BBC One HD", "url": "https://..."}``).
    """
    return await _client().patch(f"/api/channels/logos/{logo_id}/", data=fields)


@mcp.tool()
async def delete_channel_logo(logo_id: int) -> dict:
    """Delete a channel logo entry by ID."""
    return await _client().delete(f"/api/channels/logos/{logo_id}/")


@mcp.tool()
async def bulk_delete_channel_logos(ids: list[int]) -> dict:
    """Delete multiple channel logos in one request.

    `ids` is a list of integer logo IDs to remove.
    """
    return await _client().delete("/api/channels/logos/bulk-delete/", data={"ids": ids})


@mcp.tool()
async def cleanup_channel_logos() -> dict:
    """Delete all channel logos that are not assigned to any channel.

    Useful for tidying up logos that were imported or uploaded but never
    used. Returns the number of logos removed.
    """
    return await _client().post("/api/channels/logos/cleanup/", data={})


# ---------------------------------------------------------------------------
# PROXY EXTRAS — HLS and VOD proxy control
# ---------------------------------------------------------------------------


@mcp.tool()
async def change_hls_stream(channel_id: str) -> dict:
    """Force an HLS channel to switch to its next available stream source.

    Use this when an HLS stream is failing or buffering — Dispatcharr will
    immediately try the next source in the failover list.
    `channel_id` is the channel's string identifier used by the proxy.
    """
    return await _client().post(f"/proxy/hls/change_stream/{channel_id}")


@mcp.tool()
async def get_vod_proxy_stats() -> dict:
    """Get live statistics for all active VOD proxy sessions.

    Returns session counts, content being streamed, and bandwidth metrics
    for every VOD stream currently in progress.
    """
    return await _client().get("/proxy/vod/stats/")


@mcp.tool()
async def stop_vod_client() -> dict:
    """Stop a VOD client connection using the stop signal mechanism.

    Sends a stop signal to terminate an active VOD client session.
    """
    return await _client().post("/proxy/vod/stop_client/", data={})


# ---------------------------------------------------------------------------
# DVR — get_recurring_rule and bulk series rule removal
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_recurring_rule(rule_id: int) -> dict:
    """Get a single recurring DVR recording rule by ID."""
    return await _client().get(f"/api/channels/recurring-rules/{rule_id}/")


@mcp.tool()
async def bulk_remove_series_rules(tvg_ids: list[str]) -> dict:
    """Delete future scheduled recordings for one or more series rules.

    `tvg_ids` is a list of TVG-ID strings whose queued (not yet started)
    recordings should be removed.  Useful for cancelling a rule's upcoming
    recordings without fully deleting the rule itself.
    """
    return await _client().post(
        "/api/channels/series-rules/bulk-remove/", data={"tvg_ids": tvg_ids}
    )


# ---------------------------------------------------------------------------
# VOD EXTRAS — unified VOD list, categories, episodes, provider info
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_all_vod(
    search: str | None = None,
    ordering: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List all VOD content (movies and series) in a single unified list.

    Use `search` to filter by title, `ordering` to sort (e.g. ``"title"``
    or ``"-year"``), and `page`/`page_size` for pagination.
    """
    return await _client().get(
        "/api/vod/all/",
        params=_clean(
            {"search": search, "ordering": ordering, "page": page, "page_size": page_size}
        ),
    )


@mcp.tool()
async def get_vod_item(item_id: int) -> dict:
    """Get a single VOD item (movie or series) from the unified VOD list by ID."""
    return await _client().get(f"/api/vod/all/{item_id}/")


@mcp.tool()
async def get_vod_category(category_id: int) -> dict:
    """Get a single VOD category by ID."""
    return await _client().get(f"/api/vod/categories/{category_id}/")


@mcp.tool()
async def get_episode(episode_id: int) -> dict:
    """Get details for a specific VOD episode by ID."""
    return await _client().get(f"/api/vod/episodes/{episode_id}/")


@mcp.tool()
async def get_series_episodes(series_id: int) -> list:
    """Get all episodes belonging to a TV series.

    Returns the full episode list for the given series, grouped by season
    where the API supports it.
    """
    return await _client().get(f"/api/vod/series/{series_id}/episodes/")


@mcp.tool()
async def get_movie_provider_info(movie_id: int) -> dict:
    """Get external provider metadata for a VOD movie.

    Returns data from the configured metadata provider (e.g. TMDB/TVDB)
    for the given movie, including synopsis, cast, artwork URLs, and ratings.
    """
    return await _client().get(f"/api/vod/movies/{movie_id}/provider-info/")


@mcp.tool()
async def get_series_provider_info(series_id: int) -> dict:
    """Get external provider metadata for a VOD TV series.

    Returns data from the configured metadata provider (e.g. TMDB/TVDB)
    for the given series, including synopsis, cast, artwork URLs, and ratings.
    """
    return await _client().get(f"/api/vod/series/{series_id}/provider-info/")


# ---------------------------------------------------------------------------
# VOD LOGOS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_vod_logos(
    search: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List VOD logo entries stored in Dispatcharr.

    VOD logos are artwork images associated with movies and series.
    Use `search` to filter by name, and `page`/`page_size` for pagination.
    """
    return await _client().get(
        "/api/vod/vodlogos/",
        params=_clean({"search": search, "page": page, "page_size": page_size}),
    )


@mcp.tool()
async def get_vod_logo(logo_id: int) -> dict:
    """Get a single VOD logo entry by ID."""
    return await _client().get(f"/api/vod/vodlogos/{logo_id}/")


@mcp.tool()
async def create_vod_logo(name: str, url: str) -> dict:
    """Create a VOD logo entry from a remote URL.

    `name` is a human-readable label.
    `url` is the public HTTP(S) URL of the logo image.
    Dispatcharr will cache the image server-side.
    """
    return await _client().post("/api/vod/vodlogos/", data={"name": name, "url": url})


@mcp.tool()
async def update_vod_logo(logo_id: int, fields: dict) -> dict:
    """Partially update a VOD logo entry.

    Pass any subset of logo fields as `fields`
    (e.g. ``{"name": "Better Call Saul", "url": "https://..."}``).
    """
    return await _client().patch(f"/api/vod/vodlogos/{logo_id}/", data=fields)


@mcp.tool()
async def delete_vod_logo(logo_id: int) -> dict:
    """Delete a VOD logo entry by ID."""
    return await _client().delete(f"/api/vod/vodlogos/{logo_id}/")


@mcp.tool()
async def bulk_delete_vod_logos(ids: list[int]) -> dict:
    """Delete multiple VOD logos in one request.

    `ids` is a list of integer logo IDs to remove.
    """
    return await _client().delete("/api/vod/vodlogos/bulk-delete/", data={"ids": ids})


@mcp.tool()
async def cleanup_vod_logos() -> dict:
    """Delete all VOD logos that are not assigned to any movie or series.

    Useful for tidying up logos that were imported or uploaded but never
    used. Returns the number of logos removed.
    """
    return await _client().post("/api/vod/vodlogos/cleanup/", data={})


# ---------------------------------------------------------------------------
# PLUGINS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_plugins() -> dict:
    """List all installed Dispatcharr plugins.

    Returns a dict of installed plugins keyed by plugin key, including
    enabled state, version, description, and available actions.
    """
    return await _client().get("/api/plugins/plugins/")


@mcp.tool()
async def enable_plugin(key: str) -> dict:
    """Toggle the enabled/disabled state of a plugin.

    `key` is the plugin's unique string identifier (e.g. ``"my_plugin"``).
    Sends a POST to the plugin's enabled endpoint; the server toggles the
    current state and returns the new enabled status.
    """
    return await _client().post(f"/api/plugins/plugins/{key}/enabled/", data={})


@mcp.tool()
async def run_plugin(key: str) -> dict:
    """Manually trigger a plugin's main action.

    `key` is the plugin's unique string identifier.  The exact behaviour
    depends on the plugin — consult `list_plugins` for what each plugin does.
    """
    return await _client().post(f"/api/plugins/plugins/{key}/run/", data={})


@mcp.tool()
async def configure_plugin(key: str, settings: dict) -> dict:
    """Save configuration settings for a plugin.

    `key` is the plugin's unique string identifier.
    `settings` is a dict of key/value pairs — the accepted fields depend on
    the individual plugin.  Consult the plugin's documentation or the
    Dispatcharr web UI for the expected schema.
    """
    return await _client().post(f"/api/plugins/plugins/{key}/settings/", data=settings)


@mcp.tool()
async def import_plugin(data: dict | None = None) -> dict:
    """Import a plugin into Dispatcharr.

    `data` is an optional dict of import parameters (e.g. source URL or
    plugin manifest).  The exact fields depend on the plugin being imported.
    """
    return await _client().post("/api/plugins/plugins/import/", data=data or {})


@mcp.tool()
async def reload_plugins() -> dict:
    """Reload all installed plugins without restarting Dispatcharr.

    Use this after manually editing plugin files or after an import to
    pick up any changes.
    """
    return await _client().post("/api/plugins/plugins/reload/", data={})


@mcp.tool()
async def delete_plugin(key: str) -> dict:
    """Delete an installed plugin by key.

    `key` is the plugin's unique string identifier.
    This removes the plugin and its configuration from Dispatcharr.
    """
    return await _client().delete(f"/api/plugins/plugins/{key}/delete/")


@mcp.tool()
async def list_plugin_repos() -> list:
    """List all configured plugin repositories."""
    return await _client().get("/api/plugins/repos/")


@mcp.tool()
async def create_plugin_repo(url: str, public_key: str | None = None) -> dict:
    """Add a new plugin repository by manifest URL.

    `url` is the URL of the repository manifest.  Dispatcharr fetches
    and validates the manifest on creation.
    `public_key` is the optional PGP public key used to verify plugin
    signatures from this repository.
    """
    return await _client().post(
        "/api/plugins/repos/", data=_clean({"url": url, "public_key": public_key})
    )


@mcp.tool()
async def update_plugin_repo(repo_id: int, fields: dict) -> dict:
    """Update a plugin repository configuration.

    `repo_id` is the integer ID of the repository.
    Pass the full updated configuration as `fields`
    (e.g. ``{"url": "https://...", "public_key": "...", "enabled": True}``).
    """
    return await _client().put(f"/api/plugins/repos/{repo_id}/", data=fields)


@mcp.tool()
async def delete_plugin_repo(repo_id: int) -> dict:
    """Remove a plugin repository by ID.

    This removes the repository registration from Dispatcharr.  Plugins
    already installed from this repo are not automatically removed.
    """
    return await _client().delete(f"/api/plugins/repos/{repo_id}/")


# ---------------------------------------------------------------------------
# ACCOUNTS — users, groups, permissions, API keys
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_users() -> list:
    """List all Dispatcharr user accounts."""
    return await _client().get("/api/accounts/users/")


@mcp.tool()
async def get_user(user_id: int) -> dict:
    """Get a single user by ID."""
    return await _client().get(f"/api/accounts/users/{user_id}/")


@mcp.tool()
async def create_user(
    username: str,
    password: str,
    email: str | None = None,
    is_staff: bool = False,
    is_active: bool = True,
) -> dict:
    """Create a new Dispatcharr user account."""
    data: dict = {
        "username": username,
        "password": password,
        "is_staff": is_staff,
        "is_active": is_active,
    }
    if email is not None:
        data["email"] = email
    return await _client().post("/api/accounts/users/", data=data)


@mcp.tool()
async def update_user(user_id: int, fields: dict) -> dict:
    """Partially update a user account.

    Pass any subset of user fields as `fields`
    (e.g. ``{"email": "new@example.com", "is_active": False}``).
    """
    return await _client().patch(f"/api/accounts/users/{user_id}/", data=fields)


@mcp.tool()
async def delete_user(user_id: int) -> dict:
    """Delete a user account by ID."""
    return await _client().delete(f"/api/accounts/users/{user_id}/")


@mcp.tool()
async def get_current_user() -> dict:
    """Get the currently authenticated user's profile."""
    return await _client().get("/api/accounts/users/me/")


@mcp.tool()
async def update_current_user(fields: dict) -> dict:
    """Update the currently authenticated user's own profile.

    Pass any subset of user fields as `fields`
    (e.g. ``{"email": "me@example.com"}``).
    """
    return await _client().patch("/api/accounts/users/me/", data=fields)


@mcp.tool()
async def list_user_groups() -> list:
    """List all user permission groups."""
    return await _client().get("/api/accounts/groups/")


@mcp.tool()
async def get_user_group(group_id: int) -> dict:
    """Get a single user permission group by ID."""
    return await _client().get(f"/api/accounts/groups/{group_id}/")


@mcp.tool()
async def create_user_group(name: str) -> dict:
    """Create a new user permission group."""
    return await _client().post("/api/accounts/groups/", data={"name": name})


@mcp.tool()
async def update_user_group(group_id: int, fields: dict) -> dict:
    """Partially update a user permission group."""
    return await _client().patch(f"/api/accounts/groups/{group_id}/", data=fields)


@mcp.tool()
async def delete_user_group(group_id: int) -> dict:
    """Delete a user permission group by ID."""
    return await _client().delete(f"/api/accounts/groups/{group_id}/")


@mcp.tool()
async def list_permissions() -> list:
    """List all available permissions in the system."""
    return await _client().get("/api/accounts/permissions/")


@mcp.tool()
async def list_api_keys() -> list:
    """List all API keys for the current user."""
    return await _client().get("/api/accounts/api-keys/")


@mcp.tool()
async def generate_api_key() -> dict:
    """Generate a new API key for the current user."""
    return await _client().post("/api/accounts/api-keys/generate/", data={})


@mcp.tool()
async def revoke_api_key(key: str) -> dict:
    """Revoke an API key.

    `key` is the API key string to revoke.
    """
    return await _client().post("/api/accounts/api-keys/revoke/", data={"key": key})


# ---------------------------------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_notifications(
    page: int | None = None,
    page_size: int | None = None,
) -> dict:
    """List system notifications."""
    return await _client().get(
        "/api/core/notifications/",
        params=_clean({"page": page, "page_size": page_size}),
    )


@mcp.tool()
async def get_notification(notification_id: int) -> dict:
    """Get a single notification by ID."""
    return await _client().get(f"/api/core/notifications/{notification_id}/")


@mcp.tool()
async def get_notification_count() -> dict:
    """Get the count of unread/active notifications."""
    return await _client().get("/api/core/notifications/count/")


@mcp.tool()
async def dismiss_notification(notification_id: int) -> dict:
    """Dismiss (mark as read) a single notification by ID."""
    return await _client().post(
        f"/api/core/notifications/{notification_id}/dismiss/", data={}
    )


@mcp.tool()
async def dismiss_all_notifications() -> dict:
    """Dismiss all active notifications at once."""
    return await _client().post("/api/core/notifications/dismiss-all/", data={})


@mcp.tool()
async def delete_notification(notification_id: int) -> dict:
    """Delete a notification by ID."""
    return await _client().delete(f"/api/core/notifications/{notification_id}/")


# ---------------------------------------------------------------------------
# STREAM PROFILES — full CRUD
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_stream_profile(profile_id: int) -> dict:
    """Get a single stream profile by ID."""
    return await _client().get(f"/api/core/streamprofiles/{profile_id}/")


@mcp.tool()
async def create_stream_profile(
    name: str,
    parameters: str | None = None,
    profile_type: str | None = None,
) -> dict:
    """Create a new stream profile (FFmpeg/Streamlink/VLC output configuration).

    `parameters` is the FFmpeg/encoder parameters string.
    `profile_type` is one of ``"ffmpeg"``, ``"streamlink"``, ``"vlc"``, etc.
    """
    data: dict = {"name": name}
    if parameters is not None:
        data["parameters"] = parameters
    if profile_type is not None:
        data["profile_type"] = profile_type
    return await _client().post("/api/core/streamprofiles/", data=data)


@mcp.tool()
async def update_stream_profile(profile_id: int, fields: dict) -> dict:
    """Partially update a stream profile.

    Pass any subset of profile fields as `fields`
    (e.g. ``{"name": "HQ FFMPEG", "parameters": "-c:v copy"}``).
    """
    return await _client().patch(f"/api/core/streamprofiles/{profile_id}/", data=fields)


@mcp.tool()
async def delete_stream_profile(profile_id: int) -> dict:
    """Delete a stream profile by ID."""
    return await _client().delete(f"/api/core/streamprofiles/{profile_id}/")


# ---------------------------------------------------------------------------
# USERAGENTS
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_useragents() -> list:
    """List all configured user-agent strings."""
    return await _client().get("/api/core/useragents/")


@mcp.tool()
async def get_useragent(useragent_id: int) -> dict:
    """Get a single user-agent by ID."""
    return await _client().get(f"/api/core/useragents/{useragent_id}/")


@mcp.tool()
async def create_useragent(name: str, user_agent_string: str) -> dict:
    """Create a new user-agent string entry.

    `name` is a friendly label; `user_agent_string` is the raw UA header value.
    """
    return await _client().post(
        "/api/core/useragents/",
        data={"name": name, "user_agent_string": user_agent_string},
    )


@mcp.tool()
async def update_useragent(useragent_id: int, fields: dict) -> dict:
    """Partially update a user-agent entry."""
    return await _client().patch(f"/api/core/useragents/{useragent_id}/", data=fields)


@mcp.tool()
async def delete_useragent(useragent_id: int) -> dict:
    """Delete a user-agent entry by ID."""
    return await _client().delete(f"/api/core/useragents/{useragent_id}/")


@mcp.tool()
async def list_timezones() -> list:
    """List all supported timezone strings."""
    return await _client().get("/api/core/timezones/")


# ---------------------------------------------------------------------------
# CONNECT — integrations, subscriptions, logs
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_integration(integration_id: int) -> dict:
    """Get a single Connect integration by ID."""
    return await _client().get(f"/api/connect/integrations/{integration_id}/")


@mcp.tool()
async def create_integration(
    name: str,
    integration_type: str,
    url: str | None = None,
    is_active: bool = True,
    config: dict | None = None,
) -> dict:
    """Create a new Connect integration (webhook, API callback, script).

    `integration_type` is the integration kind (e.g. ``"webhook"``).
    `url` is the target endpoint URL for webhook integrations.
    `config` is an optional dict of integration-specific settings.
    """
    data: dict = {"name": name, "integration_type": integration_type, "is_active": is_active}
    if url is not None:
        data["url"] = url
    if config is not None:
        data["config"] = config
    return await _client().post("/api/connect/integrations/", data=data)


@mcp.tool()
async def update_integration(integration_id: int, fields: dict) -> dict:
    """Partially update a Connect integration."""
    return await _client().patch(
        f"/api/connect/integrations/{integration_id}/", data=fields
    )


@mcp.tool()
async def delete_integration(integration_id: int) -> dict:
    """Delete a Connect integration by ID."""
    return await _client().delete(f"/api/connect/integrations/{integration_id}/")


@mcp.tool()
async def test_integration(integration_id: int) -> dict:
    """Send a test event to a Connect integration to verify connectivity."""
    return await _client().post(
        f"/api/connect/integrations/{integration_id}/test/", data={}
    )


@mcp.tool()
async def get_integration_subscriptions(integration_id: int) -> list:
    """Get the event subscriptions for a specific integration."""
    return await _client().get(
        f"/api/connect/integrations/{integration_id}/subscriptions/"
    )


@mcp.tool()
async def set_integration_subscriptions(
    integration_id: int, subscription_ids: list[int]
) -> dict:
    """Replace the full set of event subscriptions for an integration.

    `subscription_ids` is the complete list of subscription IDs that should
    be active for this integration after the call.
    """
    return await _client().put(
        f"/api/connect/integrations/{integration_id}/subscriptions/set/",
        data={"subscription_ids": subscription_ids},
    )


@mcp.tool()
async def list_subscriptions() -> list:
    """List all Connect event subscription types."""
    return await _client().get("/api/connect/subscriptions/")


@mcp.tool()
async def get_subscription(subscription_id: int) -> dict:
    """Get a single Connect subscription by ID."""
    return await _client().get(f"/api/connect/subscriptions/{subscription_id}/")


@mcp.tool()
async def create_subscription(event_type: str, fields: dict | None = None) -> dict:
    """Create a new Connect event subscription.

    `event_type` is the event name to subscribe to.
    `fields` can supply any additional subscription fields.
    """
    data: dict = {"event_type": event_type}
    if fields:
        data.update(fields)
    return await _client().post("/api/connect/subscriptions/", data=data)


@mcp.tool()
async def update_subscription(subscription_id: int, fields: dict) -> dict:
    """Partially update a Connect subscription."""
    return await _client().patch(
        f"/api/connect/subscriptions/{subscription_id}/", data=fields
    )


@mcp.tool()
async def delete_subscription(subscription_id: int) -> dict:
    """Delete a Connect subscription by ID."""
    return await _client().delete(f"/api/connect/subscriptions/{subscription_id}/")


@mcp.tool()
async def get_delivery_log(log_id: int) -> dict:
    """Get a single stream delivery/webhook log entry by ID."""
    return await _client().get(f"/api/connect/logs/{log_id}/")


# ---------------------------------------------------------------------------
# RECORDINGS — gaps (update, metadata, comskip, artwork)
# ---------------------------------------------------------------------------


@mcp.tool()
async def update_recording(recording_id: int, fields: dict) -> dict:
    """Partially update a DVR recording's metadata fields.

    Pass any subset of recording fields as `fields`
    (e.g. ``{"title": "Better Title", "description": "…"}``).
    """
    return await _client().patch(
        f"/api/channels/recordings/{recording_id}/", data=fields
    )


@mcp.tool()
async def update_recording_metadata(recording_id: int) -> dict:
    """Trigger an automatic metadata refresh for a recording from online sources."""
    return await _client().post(
        f"/api/channels/recordings/{recording_id}/update-metadata/", data={}
    )


@mcp.tool()
async def refresh_recording_artwork(recording_id: int) -> dict:
    """Re-fetch and update the poster/thumbnail artwork for a recording."""
    return await _client().post(
        f"/api/channels/recordings/{recording_id}/refresh-artwork/", data={}
    )


@mcp.tool()
async def run_comskip(recording_id: int) -> dict:
    """Run comskip (commercial detection) on a recording.

    Requires comskip to be configured in DVR settings.
    """
    return await _client().post(
        f"/api/channels/recordings/{recording_id}/comskip/", data={}
    )


@mcp.tool()
async def bulk_delete_upcoming_recordings() -> dict:
    """Delete all upcoming (not yet started) scheduled recordings."""
    return await _client().post("/api/channels/recordings/bulk-delete-upcoming/", data={})


@mcp.tool()
async def get_comskip_config() -> dict:
    """Get the current DVR comskip configuration."""
    return await _client().get("/api/channels/dvr/comskip-config/")


@mcp.tool()
async def update_comskip_config(fields: dict) -> dict:
    """Update the DVR comskip configuration.

    Pass comskip config fields as `fields`
    (e.g. ``{"ini_content": "...", "enabled": True}``).
    """
    return await _client().post("/api/channels/dvr/comskip-config/", data=fields)


# ---------------------------------------------------------------------------
# M3U GAPS — server-groups, account profiles, refresh-vod, group-settings
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_m3u_server_groups() -> list:
    """List all M3U server groups."""
    return await _client().get("/api/m3u/server-groups/")


@mcp.tool()
async def get_m3u_server_group(group_id: int) -> dict:
    """Get a single M3U server group by ID."""
    return await _client().get(f"/api/m3u/server-groups/{group_id}/")


@mcp.tool()
async def create_m3u_server_group(name: str) -> dict:
    """Create a new M3U server group."""
    return await _client().post("/api/m3u/server-groups/", data={"name": name})


@mcp.tool()
async def update_m3u_server_group(group_id: int, fields: dict) -> dict:
    """Partially update an M3U server group."""
    return await _client().patch(f"/api/m3u/server-groups/{group_id}/", data=fields)


@mcp.tool()
async def delete_m3u_server_group(group_id: int) -> dict:
    """Delete an M3U server group by ID."""
    return await _client().delete(f"/api/m3u/server-groups/{group_id}/")


@mcp.tool()
async def list_m3u_account_profiles(account_id: int) -> list:
    """List all stream profiles configured for a specific M3U account."""
    return await _client().get(f"/api/m3u/accounts/{account_id}/profiles/")


@mcp.tool()
async def get_m3u_account_profile(account_id: int, profile_id: int) -> dict:
    """Get a single M3U account profile by account ID and profile ID."""
    return await _client().get(
        f"/api/m3u/accounts/{account_id}/profiles/{profile_id}/"
    )


@mcp.tool()
async def create_m3u_account_profile(account_id: int, fields: dict) -> dict:
    """Create a new profile for an M3U account.

    `fields` should include at minimum a ``name`` and any profile-specific
    configuration (e.g. stream limits, output format).
    """
    return await _client().post(
        f"/api/m3u/accounts/{account_id}/profiles/", data=fields
    )


@mcp.tool()
async def update_m3u_account_profile(
    account_id: int, profile_id: int, fields: dict
) -> dict:
    """Partially update an M3U account profile."""
    return await _client().patch(
        f"/api/m3u/accounts/{account_id}/profiles/{profile_id}/", data=fields
    )


@mcp.tool()
async def delete_m3u_account_profile(account_id: int, profile_id: int) -> dict:
    """Delete an M3U account profile by account ID and profile ID."""
    return await _client().delete(
        f"/api/m3u/accounts/{account_id}/profiles/{profile_id}/"
    )


@mcp.tool()
async def get_m3u_filter(account_id: int, filter_id: int) -> dict:
    """Get a single M3U stream filter by account ID and filter ID."""
    return await _client().get(
        f"/api/m3u/accounts/{account_id}/filters/{filter_id}/"
    )


@mcp.tool()
async def refresh_m3u_vod(account_id: int) -> dict:
    """Trigger a VOD library refresh for an M3U account.

    Re-imports movies, series, and episodes from the account's playlist.
    """
    return await _client().post(f"/api/m3u/accounts/{account_id}/refresh-vod/", data={})


@mcp.tool()
async def update_m3u_group_settings(account_id: int, fields: dict) -> dict:
    """Update group-level settings for an M3U account.

    `fields` contains the group settings mapping to apply
    (e.g. enabling/disabling specific groups from the playlist).
    """
    return await _client().patch(
        f"/api/m3u/accounts/{account_id}/group-settings/", data=fields
    )


@mcp.tool()
async def refresh_all_m3u_accounts() -> dict:
    """Trigger a refresh of all configured M3U accounts simultaneously."""
    return await _client().post("/api/m3u/refresh/", data={})


@mcp.tool()
async def get_m3u_auto_channels_count(account_id: int) -> dict:
    """Preview how many auto-created channels would be removed if an M3U account
    were deleted with the cleanup_channels option enabled.

    Returns the count without making any changes.
    """
    return await _client().get(
        f"/api/m3u/accounts/{account_id}/auto-created-channels-count/"
    )


@mcp.tool()
async def repack_m3u_group(
    account_id: int,
    channel_group_id: int,
) -> dict:
    """Re-pack visible channels in an M3U account group into the group's [start, end] range.

    This redistributes channel numbers evenly across the group's configured
    number range without changing stream assignments.
    """
    return await _client().post(
        f"/api/m3u/accounts/{account_id}/repack-group/",
        params={"channel_group_id": channel_group_id},
        data={},
    )


# ---------------------------------------------------------------------------
# STREAMS CRUD (Tier 2)
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_stream(
    name: str,
    url: str | None = None,
    m3u_account: int | None = None,
    channel_group: int | None = None,
    tvg_id: str | None = None,
    logo_url: str | None = None,
    is_adult: bool = False,
    stream_profile_id: int | None = None,
) -> dict:
    """Create a custom stream entry.

    Useful for adding streams that are not imported from an M3U account.
    Supply at minimum a `name`; `url` is required for the stream to be playable.
    """
    data: dict = {"name": name, "is_adult": is_adult}
    if url is not None:
        data["url"] = url
    if m3u_account is not None:
        data["m3u_account"] = m3u_account
    if channel_group is not None:
        data["channel_group"] = channel_group
    if tvg_id is not None:
        data["tvg_id"] = tvg_id
    if logo_url is not None:
        data["logo_url"] = logo_url
    if stream_profile_id is not None:
        data["stream_profile_id"] = stream_profile_id
    return await _client().post("/api/channels/streams/", data=data)


@mcp.tool()
async def update_stream(stream_id: int, fields: dict) -> dict:
    """Partially update a stream entry.

    Pass any subset of stream fields as `fields`
    (e.g. ``{"name": "BBC HD", "url": "https://...", "tvg_id": "bbc1.uk"}``).
    """
    return await _client().patch(f"/api/channels/streams/{stream_id}/", data=fields)


@mcp.tool()
async def delete_stream(stream_id: int) -> dict:
    """Delete a stream entry by ID."""
    return await _client().delete(f"/api/channels/streams/{stream_id}/")


@mcp.tool()
async def bulk_delete_streams(ids: list[int]) -> dict:
    """Delete multiple streams in a single operation.

    `ids` is a list of integer stream IDs to delete.
    """
    return await _client().delete_with_body(
        "/api/channels/streams/bulk-delete/", data={"ids": ids}
    )


@mcp.tool()
async def list_stream_groups(
    m3u_account: int | None = None,
) -> list:
    """List stream group names imported from M3U provider accounts.

    Optionally filter by `m3u_account` ID to see groups from a single provider.
    """
    return await _client().get(
        "/api/channels/streams/groups/",
        params=_clean({"m3u_account": m3u_account}),
    )


@mcp.tool()
async def list_stream_filter_options() -> dict:
    """Get available filter option values for the streams list.

    Returns the distinct values available for filtering (accounts, groups, etc.)
    — useful for building filter UIs or narrowing stream queries.
    """
    return await _client().get("/api/channels/streams/filter-options/")


@mcp.tool()
async def list_stream_ids(
    search: str | None = None,
    m3u_account: int | None = None,
    channel_group_name: str | None = None,
) -> list:
    """Get just the IDs of streams matching optional filters.

    Lightweight alternative to `list_streams` when you only need IDs,
    e.g. to pass to `bulk_delete_streams` or `get_streams_by_ids`.
    """
    return await _client().get(
        "/api/channels/streams/ids/",
        params=_clean(
            {
                "search": search,
                "m3u_account": m3u_account,
                "channel_group_name": channel_group_name,
            }
        ),
    )


@mcp.tool()
async def get_streams_by_ids(ids: list[int]) -> list:
    """Fetch full stream details for a specific list of stream IDs.

    Use this to efficiently retrieve a known set of streams by ID
    (avoids the URL-length limitation of query-string approaches).
    """
    return await _client().post(
        "/api/channels/streams/by-ids/", data={"ids": ids}
    )


# ---------------------------------------------------------------------------
# CHANNEL BULK OPERATIONS (Tier 2)
# ---------------------------------------------------------------------------


@mcp.tool()
async def bulk_delete_channels(ids: list[int]) -> dict:
    """Delete multiple channels in a single operation.

    `ids` is a list of integer channel IDs to delete permanently.
    """
    return await _client().delete_with_body(
        "/api/channels/channels/bulk-delete/", data={"ids": ids}
    )


@mcp.tool()
async def bulk_update_channels(updates: list[dict]) -> dict:
    """Update multiple channels in a single operation.

    `updates` is a list of partial channel objects — each must include an
    ``id`` field plus the fields to change
    (e.g. ``[{"id": 1, "name": "BBC One"}, {"id": 2, "channel_number": 2}]``).
    """
    return await _client().patch(
        "/api/channels/channels/edit/bulk/", data=updates
    )


@mcp.tool()
async def bulk_regex_update_channels(
    channel_ids: list[int],
    find: str,
    replace: str,
    flags: str | None = None,
) -> dict:
    """Rename multiple channels using a regex find-and-replace.

    `find` is the regex pattern to match in each channel name.
    `replace` is the replacement string (supports capture-group references).
    `flags` is an optional string of regex flags (e.g. ``"i"`` for case-insensitive).
    """
    return await _client().post(
        "/api/channels/channels/edit/bulk-regex/",
        data=_clean(
            {
                "channel_ids": channel_ids,
                "find": find,
                "replace": replace,
                "flags": flags,
            }
        ),
    )


@mcp.tool()
async def assign_channels(
    channel_ids: list[int],
    starting_number: float | None = None,
) -> dict:
    """Assign sequential channel numbers to a list of channels.

    Channels in `channel_ids` will be numbered consecutively starting from
    `starting_number` (e.g. 100.0). If `starting_number` is omitted the API
    picks the next available number.
    """
    return await _client().post(
        "/api/channels/channels/assign/",
        data=_clean({"channel_ids": channel_ids, "starting_number": starting_number}),
    )


@mcp.tool()
async def batch_set_epg(associations: list[dict]) -> dict:
    """Set EPG data associations for multiple channels at once.

    `associations` is a list of mappings, each containing a channel identifier
    and an EPG data entry ID
    (e.g. ``[{"channel_id": 1, "epg_data_id": 42}, ...]``).
    """
    return await _client().post(
        "/api/channels/channels/batch-set-epg/",
        data={"associations": associations},
    )


@mcp.tool()
async def match_epg_all(channel_ids: list[int] | None = None) -> dict:
    """Auto-match channels to EPG data using name/TVG-ID heuristics.

    Pass `channel_ids` to limit matching to specific channels, or omit to
    run the auto-matcher across all channels.
    """
    return await _client().post(
        "/api/channels/channels/match-epg/",
        data=_clean({"channel_ids": channel_ids}),
    )


@mcp.tool()
async def set_logos_from_epg() -> dict:
    """Update channel logos from their matched EPG data for all channels.

    Any channel that has an EPG association will have its logo URL replaced
    with the artwork URL from the EPG entry.
    """
    return await _client().post("/api/channels/channels/set-logos-from-epg/", data={})


@mcp.tool()
async def set_names_from_epg() -> dict:
    """Update channel names from their matched EPG data for all channels."""
    return await _client().post("/api/channels/channels/set-names-from-epg/", data={})


@mcp.tool()
async def set_tvg_ids_from_epg() -> dict:
    """Update channel TVG-IDs from their matched EPG data for all channels."""
    return await _client().post("/api/channels/channels/set-tvg-ids-from-epg/", data={})


@mcp.tool()
async def create_channels_from_streams_bulk(
    stream_ids: list[int],
    channel_profile_ids: list[int] | None = None,
    starting_channel_number: float | None = None,
) -> dict:
    """Create channels in bulk from a list of existing streams.

    Each stream in `stream_ids` gets its own new channel. Optionally assign
    them to specific `channel_profile_ids` and start numbering from
    `starting_channel_number`.
    """
    return await _client().post(
        "/api/channels/channels/from-stream/bulk/",
        data=_clean(
            {
                "stream_ids": stream_ids,
                "channel_profile_ids": channel_profile_ids,
                "starting_channel_number": starting_channel_number,
            }
        ),
    )


@mcp.tool()
async def get_channels_by_uuids(uuids: list[str]) -> dict:
    """Retrieve channels by a list of UUIDs.

    Uses a POST body to avoid URL length limits when passing many UUIDs.
    Returns the same paginated channel format as `list_channels`.
    """
    return await _client().post(
        "/api/channels/channels/by-uuids/", data={"uuids": uuids}
    )


@mcp.tool()
async def reorder_channel(channel_id: int, insert_after_id: int | None = None) -> dict:
    """Move a channel to a different position in the lineup.

    `insert_after_id` is the ID of the channel that this channel should
    appear after. Omit (or pass null) to move the channel to the top of
    the list.
    """
    return await _client().post(
        f"/api/channels/channels/{channel_id}/reorder/",
        data=_clean({"insert_after_id": insert_after_id}),
    )


@mcp.tool()
async def set_channel_epg(channel_id: int, epg_data_id: int) -> dict:
    """Manually assign a specific EPG data entry to a channel.

    `epg_data_id` is the integer ID of the EPG data entry (from `list_epg_data`)
    to associate with this channel.
    """
    return await _client().post(
        f"/api/channels/channels/{channel_id}/set-epg/",
        data={"epg_data_id": epg_data_id},
    )


@mcp.tool()
async def match_channel_epg(channel_id: int) -> dict:
    """Auto-match a single channel to EPG data using name/TVG-ID heuristics."""
    return await _client().post(
        f"/api/channels/channels/{channel_id}/match-epg/", data={}
    )


# ---------------------------------------------------------------------------
# CHANNEL PROFILES — full CRUD (Tier 2)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_channel_profile(profile_id: int) -> dict:
    """Get a single channel profile by ID."""
    return await _client().get(f"/api/channels/profiles/{profile_id}/")


@mcp.tool()
async def update_channel_profile(profile_id: int, fields: dict) -> dict:
    """Partially update a channel profile.

    Pass any subset of profile fields as `fields` (e.g. ``{"name": "4K Profile"}``).
    """
    return await _client().patch(f"/api/channels/profiles/{profile_id}/", data=fields)


@mcp.tool()
async def duplicate_channel_profile(profile_id: int) -> dict:
    """Duplicate an existing channel profile, including its channel memberships.

    Returns the newly created profile.
    """
    return await _client().post(
        f"/api/channels/profiles/{profile_id}/duplicate/", data={}
    )


@mcp.tool()
async def bulk_update_profile_channels(
    profile_id: int, channels: list[dict]
) -> dict:
    """Update channel membership/settings for multiple channels in a profile.

    `channels` is a list of partial channel-profile membership objects
    (e.g. ``[{"channel_id": 1, "enabled": True}, ...]``).
    """
    return await _client().patch(
        f"/api/channels/profiles/{profile_id}/channels/bulk-update/",
        data={"channels": channels},
    )


@mcp.tool()
async def update_profile_channel(
    profile_id: int, channel_id: int, fields: dict
) -> dict:
    """Update a single channel's membership settings within a profile.

    Pass any subset of membership fields as `fields`
    (e.g. ``{"enabled": False}``).
    """
    return await _client().patch(
        f"/api/channels/profiles/{profile_id}/channels/{channel_id}/", data=fields
    )


# ---------------------------------------------------------------------------
# CORE SETTINGS — full CRUD (Tier 2)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_setting(setting_id: int) -> dict:
    """Get a single core setting by ID."""
    return await _client().get(f"/api/core/settings/{setting_id}/")


@mcp.tool()
async def update_setting(setting_id: int, fields: dict) -> dict:
    """Partially update a core setting.

    Pass any subset of setting fields as `fields`
    (e.g. ``{"value": "new-value"}``).
    """
    return await _client().patch(f"/api/core/settings/{setting_id}/", data=fields)


@mcp.tool()
async def delete_setting(setting_id: int) -> dict:
    """Delete a core setting by ID (resets it to the built-in default)."""
    return await _client().delete(f"/api/core/settings/{setting_id}/")


@mcp.tool()
async def check_settings(fields: dict | None = None) -> dict:
    """Validate the current core settings configuration.

    Optionally pass `fields` to check proposed setting values before applying them.
    Returns a validation report with any errors or warnings.
    """
    return await _client().post("/api/core/settings/check/", data=fields or {})


@mcp.tool()
async def get_env_settings() -> dict:
    """Get environment-level settings (read-only, sourced from env vars / config files)."""
    return await _client().get("/api/core/settings/env/")


@mcp.tool()
async def rehash_streams() -> dict:
    """Regenerate stream hashes for all streams.

    Forces Dispatcharr to recompute the stream hash used for deduplication.
    Useful after bulk imports or URL changes.
    """
    return await _client().post("/api/core/rehash-streams/", data={})


# ---------------------------------------------------------------------------
# EPG PROGRAMS — full CRUD (Tier 2)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_epg_program(program_id: int) -> dict:
    """Get a single EPG program schedule entry by ID."""
    return await _client().get(f"/api/epg/programs/{program_id}/")


@mcp.tool()
async def create_epg_program(
    tvg_id: str,
    start_time: str,
    end_time: str,
    title: str,
    sub_title: str | None = None,
    description: str | None = None,
) -> dict:
    """Create a new EPG program entry.

    `tvg_id` links the program to an EPG data channel.
    `start_time` and `end_time` are ISO 8601 datetime strings
    (e.g. ``"2026-05-05T20:00:00Z"``).
    """
    return await _client().post(
        "/api/epg/programs/",
        data=_clean(
            {
                "tvg_id": tvg_id,
                "start_time": start_time,
                "end_time": end_time,
                "title": title,
                "sub_title": sub_title,
                "description": description,
            }
        ),
    )


@mcp.tool()
async def update_epg_program(program_id: int, fields: dict) -> dict:
    """Partially update an EPG program entry.

    Pass any subset of program fields as `fields`
    (e.g. ``{"title": "New Title", "description": "Updated synopsis"}``).
    """
    return await _client().patch(f"/api/epg/programs/{program_id}/", data=fields)


@mcp.tool()
async def delete_epg_program(program_id: int) -> dict:
    """Delete an EPG program entry by ID."""
    return await _client().delete(f"/api/epg/programs/{program_id}/")


@mcp.tool()
async def import_epg(epgdata_id: int) -> dict:
    """Trigger an import/refresh of programs for a specific EPG data entry.

    `epgdata_id` is the ID of the EPG data record (channel metadata) whose
    program schedule should be re-fetched from its source.
    """
    return await _client().post("/api/epg/import/", data={"id": epgdata_id})


@mcp.tool()
async def get_epg_data_entry(entry_id: int) -> dict:
    """Get a single EPG data entry (channel metadata record) by ID."""
    return await _client().get(f"/api/epg/epgdata/{entry_id}/")


# ---------------------------------------------------------------------------
# CORE — OUTPUT PROFILES
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_output_profiles() -> list:
    """List all configured output profiles.

    Output profiles define the command and parameters used to transcode
    or pass-through a stream (e.g. different FFmpeg configurations for
    different client types).
    """
    return await _client().get("/api/core/outputprofiles/")


@mcp.tool()
async def get_output_profile(profile_id: int) -> dict:
    """Get a single output profile by ID."""
    return await _client().get(f"/api/core/outputprofiles/{profile_id}/")


@mcp.tool()
async def create_output_profile(
    name: str,
    command: str,
    parameters: str,
    is_active: bool = True,
) -> dict:
    """Create a new output profile.

    `command` is the executable (e.g. ``ffmpeg``).
    `parameters` are the command-line arguments — must read from ``pipe:0``
    (stdin) and write to ``pipe:1`` (stdout).
    """
    return await _client().post(
        "/api/core/outputprofiles/",
        data=_clean({
            "name": name,
            "command": command,
            "parameters": parameters,
            "is_active": is_active,
        }),
    )


@mcp.tool()
async def update_output_profile(profile_id: int, fields: dict) -> dict:
    """Partially update an output profile by ID.

    `fields` may contain any of: ``name``, ``command``, ``parameters``,
    ``is_active``. Locked (built-in) profiles cannot be modified.
    """
    return await _client().patch(
        f"/api/core/outputprofiles/{profile_id}/", data=fields
    )


@mcp.tool()
async def delete_output_profile(profile_id: int) -> dict:
    """Delete an output profile by ID.

    Built-in locked profiles cannot be deleted.
    """
    return await _client().delete(f"/api/core/outputprofiles/{profile_id}/")


# ---------------------------------------------------------------------------
# BACKUPS (Tier 2)
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_backups() -> list:
    """List all available backup files."""
    return await _client().get("/api/backups/")


@mcp.tool()
async def create_backup() -> dict:
    """Create a new backup of the Dispatcharr database and configuration.

    The backup is saved server-side and visible via `list_backups`.
    Returns a task ID that can be polled with `get_backup_status`.
    """
    return await _client().post("/api/backups/create/", data={})


@mcp.tool()
async def restore_backup(filename: str) -> dict:
    """Restore Dispatcharr from a backup file.

    `filename` is the backup filename as returned by `list_backups`.
    This will overwrite current data — use with caution.
    Returns a task ID that can be polled with `get_backup_status`.
    """
    return await _client().post(f"/api/backups/{filename}/restore/", data={})


@mcp.tool()
async def delete_backup(filename: str) -> dict:
    """Delete a backup file by filename.

    `filename` is the backup filename as returned by `list_backups`.
    This permanently removes the backup from the server.
    """
    return await _client().delete(f"/api/backups/{filename}/delete/")


@mcp.tool()
async def get_backup_schedule() -> dict:
    """Get the current automated backup schedule configuration."""
    return await _client().get("/api/backups/schedule/")


@mcp.tool()
async def update_backup_schedule(fields: dict) -> dict:
    """Update the automated backup schedule configuration.

    Pass the full schedule configuration as `fields`
    (e.g. ``{"enabled": True, "interval_hours": 24, "keep_count": 7}``).
    """
    return await _client().put("/api/backups/schedule/update/", data=fields)


@mcp.tool()
async def get_backup_status(task_id: str) -> dict:
    """Poll the status of a running backup or restore task.

    `task_id` is the task identifier returned by `create_backup` or
    `restore_backup`.
    """
    return await _client().get(f"/api/backups/status/{task_id}/")


@mcp.tool()
async def get_backup_download_token(filename: str) -> dict:
    """Get a time-limited download token for a backup file.

    `filename` is the backup filename as returned by `list_backups`.
    Returns a token that can be used to download the file without
    re-authenticating.
    """
    return await _client().get(f"/api/backups/{filename}/download-token/")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

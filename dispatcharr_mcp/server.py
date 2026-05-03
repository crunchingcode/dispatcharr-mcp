"""Dispatcharr MCP server — exposes Dispatcharr IPTV management to AI agents.

Tools are grouped by domain:
  • Accounts/Users — users, groups, permissions, API keys
  • Channels       — list, get, create, update, delete channels & groups
  • Streams        — list/get raw M3U streams by source
  • Proxy          — live stream status and control (change, stop, failover)
  • EPG            — EPG sources and programme data
  • M3U Accounts   — manage M3U provider accounts, filters, profiles, server-groups
  • VOD            — movies, series, episodes
  • System         — settings, stream profiles, useragents, system events
  • Notifications  — system notifications
  • Connect        — integrations, subscriptions, delivery logs
  • DVR            — recordings, series rules, recurring rules
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

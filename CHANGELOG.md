# Changelog

All notable changes to dispatcharr-mcp are documented here.

---

## [0.3.0] - 2026-05-03

### Added

**Accounts / Users**
- `list_users`, `get_user`, `create_user`, `update_user`, `delete_user` — full user account CRUD
- `get_current_user`, `update_current_user` — manage the authenticated user's own profile
- `list_user_groups`, `get_user_group`, `create_user_group`, `update_user_group`, `delete_user_group` — user permission group management
- `list_permissions` — list all available system permissions
- `list_api_keys`, `generate_api_key`, `revoke_api_key` — API key management

**Notifications**
- `list_notifications`, `get_notification`, `get_notification_count` — query system notifications
- `dismiss_notification`, `dismiss_all_notifications` — mark notifications as read
- `delete_notification` — remove a notification

**Stream Profiles**
- `get_stream_profile`, `create_stream_profile`, `update_stream_profile`, `delete_stream_profile` — full CRUD on stream profiles (FFmpeg/Streamlink/VLC configurations)

**Useragents**
- `list_useragents`, `get_useragent`, `create_useragent`, `update_useragent`, `delete_useragent` — manage user-agent strings
- `list_timezones` — list all supported timezones

**Connect Integrations**
- `get_integration`, `create_integration`, `update_integration`, `delete_integration` — full integration CRUD
- `test_integration` — send a test event to verify an integration
- `get_integration_subscriptions`, `set_integration_subscriptions` — manage event subscriptions per integration
- `list_subscriptions`, `get_subscription`, `create_subscription`, `update_subscription`, `delete_subscription` — manage Connect event subscriptions
- `get_delivery_log` — retrieve a single delivery/webhook log entry

**DVR Recordings (gaps)**
- `update_recording` — partially update recording metadata fields
- `update_recording_metadata` — trigger automatic metadata refresh from online sources
- `refresh_recording_artwork` — re-fetch poster/thumbnail artwork
- `run_comskip` — run commercial detection on a recording
- `bulk_delete_upcoming_recordings` — delete all not-yet-started scheduled recordings
- `get_comskip_config`, `update_comskip_config` — manage DVR comskip configuration

**M3U (gaps)**
- `list_m3u_server_groups`, `get_m3u_server_group`, `create_m3u_server_group`, `update_m3u_server_group`, `delete_m3u_server_group` — M3U server group management
- `list_m3u_account_profiles`, `get_m3u_account_profile`, `create_m3u_account_profile`, `update_m3u_account_profile`, `delete_m3u_account_profile` — per-account stream profile management
- `get_m3u_filter` — retrieve a single M3U filter by ID
- `refresh_m3u_vod` — trigger VOD library refresh for an M3U account
- `update_m3u_group_settings` — update group-level settings for an M3U account
- `refresh_all_m3u_accounts` — trigger a simultaneous refresh of all M3U accounts

### Other
- `swagger.yaml` updated to latest live schema (renamed from `swagger.json`)
- README Tools table updated; TODO section added tracking remaining unimplemented endpoints

---

## [0.2.0] - 2026-04-22

### Added

**EPG**
- `get_current_programs` — now-playing programme for all channels or a filtered list of channel UUIDs
- `get_epg_grid` — full TV guide grid covering the past hour, now, and the next 24 hours

**DVR Recordings**
- `schedule_recording` — schedule a new recording by channel ID with start/end datetimes
- `delete_recording` — delete a recording and remove the file from disk
- `stop_recording` — stop an in-progress recording early while keeping the partial file
- `extend_recording` — extend an active recording's end time without interrupting the stream

**DVR Series Rules**
- `list_series_rules` — list all configured series recording rules
- `create_series_rule` — create or update a series rule (record all or only new episodes)
- `delete_series_rule` — delete a series rule and remove its future scheduled recordings
- `evaluate_series_rules` — trigger evaluation of rules to schedule matching episodes

**DVR Recurring Rules**
- `list_recurring_rules` — list all time-based recurring recording rules
- `create_recurring_rule` — create a recurring rule (day-of-week, time window, date bounds)
- `update_recurring_rule` — partially update a recurring rule
- `delete_recurring_rule` — delete a recurring rule

**M3U Filters**
- `create_m3u_filter` — add a regex-based stream filter to an M3U account
- `update_m3u_filter` — partially update an existing M3U filter
- `delete_m3u_filter` — delete an M3U filter

**Channel Groups**
- `update_channel_group` — rename a channel group

**Channel Profiles**
- `create_channel_profile` — create a new output channel profile
- `delete_channel_profile` — delete a channel profile

**System**
- `get_version` — get the running Dispatcharr application version

---

## [0.1.1] - initial release

### Added
- Full channel CRUD: `list_channels`, `get_channel`, `create_channel`, `update_channel`, `delete_channel`, `get_channel_streams`
- Channel group management: `list_channel_groups`, `create_channel_group`, `delete_channel_group`
- Stream listing: `list_streams`, `get_stream`, `create_channel_from_stream`
- Live proxy control: `get_proxy_status`, `get_channel_proxy_status`, `change_channel_stream`, `next_channel_stream`, `stop_channel_stream`, `stop_channel_client`
- EPG source management: `list_epg_sources`, `get_epg_source`, `create_epg_source`, `update_epg_source`, `delete_epg_source`, `list_epg_data`, `list_epg_programs`
- M3U account management: `list_m3u_accounts`, `get_m3u_account`, `create_m3u_account`, `update_m3u_account`, `delete_m3u_account`, `refresh_m3u_account`, `list_m3u_filters`
- Channel profiles: `list_channel_profiles`
- VOD: `list_movies`, `get_movie`, `list_series`, `get_series`, `list_episodes`, `list_vod_categories`
- System: `get_core_settings`, `list_stream_profiles`, `get_system_events`, `list_integrations`, `list_stream_delivery_logs`
- DVR: `list_recordings`, `get_recording`
- HDHomeRun: `list_hdhr_devices`
- Auth: API key (stateless) and JWT (username/password) modes

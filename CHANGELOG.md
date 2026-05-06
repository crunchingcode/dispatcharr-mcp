# Changelog

All notable changes to dispatcharr-mcp are documented here.

---

## [1.0.0] - 2026-05-06

### Added

**Streams CRUD**
- `create_stream` — create a new stream
- `update_stream` — partially update an existing stream
- `delete_stream` — delete a stream by ID
- `bulk_delete_streams` — delete multiple streams by ID list
- `list_stream_groups` — list all stream group names
- `list_stream_filter_options` — list available filter option values for streams
- `list_stream_ids` — retrieve all stream IDs (lightweight)
- `get_streams_by_ids` — retrieve full stream objects for a list of IDs

**Channel Bulk Operations**
- `bulk_delete_channels` — delete multiple channels by ID list
- `bulk_update_channels` — bulk partial-update multiple channels in one request
- `bulk_regex_update_channels` — bulk rename channel names via server-side regex find/replace
- `assign_channels` — auto-assign channel numbers from an ordered ID list
- `batch_set_epg` — associate multiple channels with EPG data without triggering a full refresh
- `match_epg_all` — fuzzy-match channels with EPG data (optionally scoped to a list of channel IDs)
- `set_logos_from_epg` — bulk set channel logos from matched EPG data
- `set_names_from_epg` — bulk set channel names from matched EPG data
- `set_tvg_ids_from_epg` — bulk set channel TVG-IDs from matched EPG data
- `create_channels_from_streams_bulk` — asynchronously bulk-create channels from stream IDs
- `get_channels_by_uuids` — retrieve channels by UUID list (POST to avoid URL limits)
- `reorder_channel` — move a channel after another channel with automatic renumbering
- `set_channel_epg` — set EPG data for a specific channel and refresh its programmes
- `match_channel_epg` — auto-match a single channel with EPG data

**Channel Profiles (full CRUD)**
- `get_channel_profile` — retrieve a channel profile by ID
- `update_channel_profile` — partially update a channel profile
- `duplicate_channel_profile` — duplicate an existing channel profile
- `bulk_update_profile_channels` — bulk enable/disable channels for a profile
- `update_profile_channel` — enable or disable a single channel within a profile

**Core Settings (full CRUD)**
- `get_setting` — retrieve a single setting by ID
- `update_setting` — partially update a setting
- `delete_setting` — delete a setting
- `check_settings` — validate current settings
- `get_env_settings` — retrieve environment-level settings
- `rehash_streams` — trigger a stream rehash on all active proxies

**EPG Programs (full CRUD)**
- `get_epg_program` — retrieve a single EPG programme by ID
- `create_epg_program` — create a custom EPG programme entry
- `update_epg_program` — partially update an EPG programme
- `delete_epg_program` — delete an EPG programme
- `import_epg` — trigger an import for an EPG data source
- `get_epg_data_entry` — retrieve a single EPG data (source mapping) entry by ID

**Backups**
- `list_backups` — list all available backup files
- `create_backup` — create a new backup asynchronously
- `restore_backup` — restore from a backup file (async, flushes DB)
- `delete_backup` — delete a backup file
- `get_backup_schedule` — retrieve backup schedule settings
- `update_backup_schedule` — update backup schedule settings
- `get_backup_status` — check the status of a backup/restore task
- `get_backup_download_token` — get a signed token for downloading a backup file

### Changed
- `swagger.json` renamed to `swagger.yaml` (file was already YAML format)
- `DispatcharrClient` gains `put()` and `delete_with_body()` HTTP methods to support new endpoints
- README Tools table updated with all new tools; TODO section reflects remaining multipart-upload items

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

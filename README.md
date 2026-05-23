# dispatcharr-mcp

An [MCP](https://modelcontextprotocol.io) server for [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) — giving AI agents full control over your IPTV streams, channels, EPG, and VOD library.

## Authentication

Two modes are supported — `DISPATCHARR_API_KEY` takes priority if set:

| Mode | Variables needed |
|------|------------------|
| API Key (stateless, no token expiry) | `DISPATCHARR_URL` + `DISPATCHARR_API_KEY` |
| JWT (username/password) | `DISPATCHARR_URL` + `DISPATCHARR_USERNAME` + `DISPATCHARR_PASSWORD` |

To generate an API key: Dispatcharr UI → **System → Users** → edit your user → copy the API Key field.

## Tools

| Domain | Tools |
|--------|-------|
| **Accounts / Users** | `list_users`, `get_user`, `create_user`, `update_user`, `delete_user`, `get_current_user`, `update_current_user`, `list_user_groups`, `get_user_group`, `create_user_group`, `update_user_group`, `delete_user_group`, `list_permissions`, `list_api_keys`, `generate_api_key`, `revoke_api_key` |
| **Channels** | `list_channels`, `get_channel`, `create_channel`, `update_channel`, `delete_channel`, `get_channel_streams`, `get_channel_stream_stats`, `get_channels_in_number_range`, `bulk_delete_channels`, `bulk_update_channels`, `bulk_regex_update_channels`, `assign_channels`, `batch_set_epg`, `match_epg_all`, `set_logos_from_epg`, `set_names_from_epg`, `set_tvg_ids_from_epg`, `create_channels_from_streams_bulk`, `get_channels_by_uuids`, `reorder_channel`, `set_channel_epg`, `match_channel_epg` |
| **Channel Groups** | `list_channel_groups`, `create_channel_group`, `update_channel_group`, `delete_channel_group` |
| **Streams** | `list_streams`, `get_stream`, `create_channel_from_stream`, `preview_regex_streams`, `create_stream`, `update_stream`, `delete_stream`, `bulk_delete_streams`, `list_stream_groups`, `list_stream_filter_options`, `list_stream_ids`, `get_streams_by_ids` |
| **Proxy / Live** | `get_proxy_status`, `get_channel_proxy_status`, `change_channel_stream`, `next_channel_stream`, `stop_channel_stream`, `stop_channel_client` |
| **EPG** | `list_epg_sources`, `get_epg_source`, `create_epg_source`, `upload_epg_source`, `update_epg_source`, `delete_epg_source`, `list_epg_data`, `list_epg_programs`, `search_epg_programs`, `get_current_programs`, `get_epg_grid` |
| **M3U Accounts** | `list_m3u_accounts`, `get_m3u_account`, `create_m3u_account`, `update_m3u_account`, `delete_m3u_account`, `refresh_m3u_account`, `refresh_all_m3u_accounts`, `get_m3u_auto_channels_count`, `repack_m3u_group`, `refresh_m3u_vod`, `update_m3u_group_settings`, `list_m3u_filters`, `get_m3u_filter`, `create_m3u_filter`, `update_m3u_filter`, `delete_m3u_filter`, `list_m3u_account_profiles`, `get_m3u_account_profile`, `create_m3u_account_profile`, `update_m3u_account_profile`, `delete_m3u_account_profile` |
| **M3U Server Groups** | `list_m3u_server_groups`, `get_m3u_server_group`, `create_m3u_server_group`, `update_m3u_server_group`, `delete_m3u_server_group` |
| **Channel Profiles** | `list_channel_profiles`, `create_channel_profile`, `delete_channel_profile`, `get_channel_profile`, `update_channel_profile`, `duplicate_channel_profile`, `bulk_update_profile_channels`, `update_profile_channel` |
| **VOD** | `list_movies`, `get_movie`, `list_series`, `get_series`, `list_episodes`, `list_vod_categories` |
| **System** | `get_core_settings`, `get_version`, `list_stream_profiles`, `get_stream_profile`, `create_stream_profile`, `update_stream_profile`, `delete_stream_profile`, `get_system_events`, `list_timezones`, `list_useragents`, `get_useragent`, `create_useragent`, `update_useragent`, `delete_useragent`, `get_setting`, `update_setting`, `delete_setting`, `check_settings`, `get_env_settings`, `rehash_streams` |
| **Output Profiles** | `list_output_profiles`, `get_output_profile`, `create_output_profile`, `update_output_profile`, `delete_output_profile` |
| **Notifications** | `list_notifications`, `get_notification`, `get_notification_count`, `dismiss_notification`, `dismiss_all_notifications`, `delete_notification` |
| **Connect** | `list_integrations`, `get_integration`, `create_integration`, `update_integration`, `delete_integration`, `test_integration`, `get_integration_subscriptions`, `set_integration_subscriptions`, `list_subscriptions`, `get_subscription`, `create_subscription`, `update_subscription`, `delete_subscription`, `list_stream_delivery_logs`, `get_delivery_log` |
| **Channel Logos** | `list_channel_logos`, `get_channel_logo`, `create_channel_logo`, `update_channel_logo`, `delete_channel_logo`, `bulk_delete_channel_logos`, `cleanup_channel_logos` |
| **VOD extras** | `list_all_vod`, `get_vod_item`, `get_vod_category`, `get_episode`, `get_series_episodes`, `get_movie_provider_info`, `get_series_provider_info` |
| **VOD Logos** | `list_vod_logos`, `get_vod_logo`, `create_vod_logo`, `update_vod_logo`, `delete_vod_logo`, `bulk_delete_vod_logos`, `cleanup_vod_logos` |
| **HDHomeRun** | `list_hdhr_devices`, `get_hdhr_device`, `create_hdhr_device`, `update_hdhr_device`, `delete_hdhr_device` |
| **Proxy extras** | `change_hls_stream`, `get_vod_proxy_stats`, `stop_vod_client` |
| **DVR Recordings** | `list_recordings`, `get_recording`, `schedule_recording`, `update_recording`, `delete_recording`, `stop_recording`, `extend_recording`, `update_recording_metadata`, `refresh_recording_artwork`, `run_comskip`, `bulk_delete_upcoming_recordings`, `get_comskip_config`, `update_comskip_config` |
| **DVR Series Rules** | `list_series_rules`, `create_series_rule`, `delete_series_rule`, `evaluate_series_rules`, `preview_series_rule`, `bulk_remove_series_rules` |
| **DVR Recurring Rules** | `list_recurring_rules`, `get_recurring_rule`, `create_recurring_rule`, `update_recurring_rule`, `delete_recurring_rule` |
| **EPG (programs)** | `get_epg_program`, `create_epg_program`, `update_epg_program`, `delete_epg_program`, `import_epg`, `get_epg_data_entry` |
| **Backups** | `list_backups`, `create_backup`, `restore_backup`, `delete_backup`, `get_backup_schedule`, `update_backup_schedule`, `get_backup_status`, `get_backup_download_token` |
| **Plugins** | `list_plugins`, `enable_plugin`, `run_plugin`, `configure_plugin`, `import_plugin`, `reload_plugins`, `delete_plugin`, `list_plugin_repos`, `create_plugin_repo`, `update_plugin_repo`, `delete_plugin_repo` |

## TODO

The following API endpoints are not yet implemented. Contributions welcome.

### Tier 2 — Useful management operations

- **File uploads** — `upload_backup`, `upload_channel_logo` (multipart file upload, requires different client support)

### Tier 3 — Niche / lower priority

- **Plugin extras** — `refresh_plugin_repo`, `install_plugin`, `list_available_plugins`, `get_repo_settings`, `update_repo_settings`, `preview_plugin`, `get_plugin_detail` (not present in current swagger spec)

## Requirements

- Python 3.10+
- A running Dispatcharr instance (v0.20+)
- A Dispatcharr API key **or** a username + password

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/dispatcharr-mcp
cd dispatcharr-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Usage

### VS Code (`mcp.json`) — API Key (recommended)

```json
{
  "servers": {
    "dispatcharr": {
      "type": "stdio",
      "command": "/path/to/dispatcharr-mcp/.venv/bin/dispatcharr-mcp",
      "args": [],
      "env": {
        "DISPATCHARR_URL": "http://your-dispatcharr-host:9191",
        "DISPATCHARR_API_KEY": "your-api-key"
      }
    }
  }
}
```

### VS Code (`mcp.json`) — Username/Password (JWT)

```json
{
  "servers": {
    "dispatcharr": {
      "type": "stdio",
      "command": "/path/to/dispatcharr-mcp/.venv/bin/dispatcharr-mcp",
      "args": [],
      "env": {
        "DISPATCHARR_URL": "http://your-dispatcharr-host:9191",
        "DISPATCHARR_USERNAME": "mcp",
        "DISPATCHARR_PASSWORD": "your-password"
      }
    }
  }
}
```

### CLI / manual

```bash
export DISPATCHARR_URL=http://dispatcharr.local:9191
export DISPATCHARR_API_KEY=your-api-key   # or use USERNAME + PASSWORD below

.venv/bin/dispatcharr-mcp
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISPATCHARR_URL` | ✅ | Base URL of your Dispatcharr instance |
| `DISPATCHARR_API_KEY` | ✅ (or user+pass) | Static API key — preferred auth method |
| `DISPATCHARR_USERNAME` | ✅ (or api key) | Dispatcharr username (JWT fallback) |
| `DISPATCHARR_PASSWORD` | ✅ (or api key) | Dispatcharr password (JWT fallback) |

## License

MIT
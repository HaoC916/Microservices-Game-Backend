# Fishgame Client Latency Metrics

## Where Logs Appear
- Latency logs are printed in the Godot editor/runtime Output panel.
- Event logs are also printed in Output.
- Look for lines like:
  - `[EVENT] <timestamp_ms> <message>`
  - `[LATENCY] <timestamp_ms> <tag>_ms=<value>`
- Logs are also appended to: `user://cmpt756_latency_log.txt`.
- Press **F8** to print the resolved absolute log path in Output.
- On Windows, the `user://` path is typically under:
  - `%APPDATA%\Godot\app_userdata\<project_name>\cmpt756_latency_log.txt`

## What Each Metric Means
- `login_ms`: login request latency (`authenticate_email_async`).
- `create_account_ms`: create account request latency.
- `match_search_ms`: time to submit matchmaking search and receive the matchmaker ticket/response.
- `match_found_ms`: time from starting matchmaking to receiving the match-found event from Nakama socket.
- `create_match_ms`: time from create-match request to match join callback.
- `join_match_ms`: time from join-match request to match join callback.
- `telemetry_sync_ms`: extra blocking time spent posting telemetry to `admin-api` (only when `telemetry_mode=sync`).

## Telemetry Schema Note
- Client telemetry payload includes:
  - `client_mode` (`off|async|sync` from fishgame client perspective)
  - `client_tag` (`fishgame`)
- `admin-api` has its own server config `TELEMETRY_MODE` in `/config`.
- These two modes can be different and should not be mixed:
  - `client_mode` = experiment mode on the client critical path
  - `admin-api TELEMETRY_MODE` = server-side ingestion behavior

## How To Trigger Metrics
- Login on Connection screen -> `login_ms`
- Create Account on Connection screen -> `create_account_ms`
- Search Match on Match screen -> `match_search_ms`, `match_found_ms`
- Create Match on Match screen -> `create_match_ms`
- Join Match on Match screen -> `join_match_ms`
- Logout on Match screen -> `[EVENT] ... logout`

## Logout Behavior
- `Online.logout()` performs client-side cleanup:
  - Leaves/cancels ongoing matchmaking or match (if active).
  - Disconnects/clears the Nakama socket.
  - Clears session/client state and emits session change.
- Match screen Logout button triggers this and returns UI to `ConnectionScreen`.
- This makes repeated login/connect/match tests practical.

## Auto Test Mode
- Trigger key: **F9** on `MatchScreen`.
- Press once to start automation, press again to request stop.
- Per run:
  - Ensures valid session/socket.
  - Triggers normal matchmaking action.
  - Prints `[AUTOTEST] start_matchmaking`.
  - Waits for match up to timeout, then cancels and retries if not found.
- Default loop settings:
  - 20 iterations
  - 2s cooldown between iterations
  - match timeout guard per iteration
- This helps collect many `[LATENCY]` samples with minimal manual clicks.

## Hotkeys (MatchScreen)
- `F8`: Print log file path (`user://cmpt756_latency_log.txt`) as absolute path in Output.
- `F9`: Toggle AutoTest matchmaking (20 iterations, 2s cooldown, timeout + cancel + retry).
- `F10`: Toggle hotkey help overlay (optional; hidden by default).

## How To Run Experiments
- Start Nakama backend and fishgame client.
- Set `nakama_host` for your target:
  - local backend, or
  - cloud backend (via `NAKAMA_HOST` env var or `user://nakama_host.txt`).
- Set telemetry coupling mode:
  - `user://telemetry_mode.txt` with `off`, `async`, or `sync`, or
  - edit `telemetry_mode` in `fishgame-godot/autoload/Online.gd`.
- Optional Admin API host override:
  - `user://admin_api_host.txt` (falls back to `nakama_host`).
- Login on Connection screen.
- Press `F9` on Match screen to run repeated matchmaking samples.
- Press `F8` to print the absolute log file path.
- Share `cmpt756_latency_log.txt` with teammates.

## Recommended Workflow
- Run one session against local backend and one against cloud backend.
- Run `telemetry_mode=off` or `async`, then run `telemetry_mode=sync`.
- Keep test settings consistent (same AutoTest loop and runtime window).
- Collect both Godot Output snippets and the log file.
- Compare `match_search_ms` p95/p99 and tails between modes; in `sync` mode, `telemetry_sync_ms` is expected to add temporal coupling overhead.
- Aggregate `*_ms` metrics (`login_ms`, `create_account_ms`, `match_search_ms`, `match_found_ms`, `create_match_ms`, `join_match_ms`, `telemetry_sync_ms`) for comparison.

## Note
- These are client-perceived end-to-end latencies.

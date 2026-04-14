# Google Workspace CLI Setup Guide

Complete setup guide for the `gws` CLI with Drive, Gmail, and Calendar access on a Salesforce macOS machine. Follow this end-to-end to get a fully authenticated, working environment.

---

## How Authentication Works

The `gws` CLI stores OAuth credentials in `~/.config/gws/credentials.enc` — an encrypted file whose key is held in the macOS Keychain. After running `gws auth setup` once, all subsequent `gws` commands work without any token prefix, and credentials refresh automatically.

`gws auth setup` requires `gcloud` to be installed and authenticated in order to select or create the GCP project used for the OAuth client.

There is also an env-var-based approach (`GOOGLE_WORKSPACE_CLI_TOKEN`) where you pass any valid Google OAuth2 access token directly. This works for any Google Workspace API *as long as the token carries the required scopes*. The limitation is not the env var itself — it is that `gcloud auth print-access-token` only returns a token scoped for Cloud Platform (and optionally Drive with `--enable-gdrive-access`), so this fallback practically only covers Drive.

**Use the keyring approach (`gws auth setup`).** It is simpler, covers all services, and does not require prefixing every command.

---

## Prerequisites

- macOS with Homebrew
- Node.js / npm
- `gcloud` CLI
- `gws` CLI

---

## Step 1: Install gcloud CLI

```bash
brew install --cask gcloud-cli
```

> Note: `google-cloud-sdk` is a legacy alias for the same cask and still works, but `gcloud-cli` is the current canonical name.

Verify:

```bash
gcloud --version
```

---

## Step 2: Install gws CLI

```bash
npm install -g @googleworkspace/cli
```

Verify:

```bash
gws --version
```

---

## Step 3: Authenticate gcloud

`gws auth setup` requires gcloud to be authenticated first:

```bash
gcloud auth login
```

This opens a browser. Log in with your Google/Salesforce account.

---

## Step 4: Authenticate with gws

```bash
gws auth setup
```

This will interactively prompt you to select a GCP project from your accessible projects list (it calls `gcloud projects list` internally), then run the authorization flow in the browser. It will attempt to enable the Google Workspace APIs on the selected project and may log 403 errors — this is expected and harmless, the OAuth flow completes regardless.

Credentials (including the refresh token and client credentials) are stored in `~/.config/gws/credentials.enc`, encrypted with a key held in the macOS Keychain. `client_secret.json` is no longer required after setup completes.

### What NOT to do

| Command | Why to avoid |
|---|---|
| `gcloud auth application-default login` | Sets up ADC credentials that require a quota project for Drive/Gmail/Calendar, causing 403 errors |
| `gcloud auth login --enable-gdrive-access` | Only relevant for the Drive-only env var fallback — do not use as a substitute for `gws auth setup` |

---

## Step 5: Verify all three services

Run each of these. Each should return JSON data, not an error.

```bash
# Drive
gws drive files list --params '{"pageSize": 3, "fields": "files(name,mimeType)"}'

# Gmail
gws gmail users getProfile --params '{"userId": "me"}'

# Calendar
gws calendar calendarList list
```

If any return errors, see Troubleshooting below.

---

## Command Reference

All `gws` commands use two flags for parameters:

- `--params '{"key": "value"}'` — URL/query parameters (resource IDs, page size, filters)
- `--json '{"key": "value"}'` — Request body (for POST/PATCH operations)

### Drive

```bash
# List files
gws drive files list --params '{"pageSize": 10, "fields": "files(id,name,mimeType,webViewLink)"}'

# Search files by content
gws drive files list --params '{"q": "fullText contains '\''keyword'\''", "pageSize": 10, "fields": "files(id,name,mimeType,webViewLink,modifiedTime)"}'

# Filter by type (append to q)
# Google Docs:   and mimeType = 'application/vnd.google-apps.document'
# Sheets:        and mimeType = 'application/vnd.google-apps.spreadsheet'
# Slides:        and mimeType = 'application/vnd.google-apps.presentation'

# Fetch a Google Doc (full JSON with hyperlinks preserved)
gws docs documents get --params '{"documentId": "<FILE_ID>"}'

# Fetch a Google Sheet
gws sheets spreadsheets get --params '{"spreadsheetId": "<SHEET_ID>", "includeGridData": true}'

# Fetch a Google Slides presentation
gws slides presentations get --params '{"presentationId": "<SLIDE_ID>"}'
```

### Gmail

```bash
# Get profile (good auth check)
gws gmail users getProfile --params '{"userId": "me"}'

# Search messages
gws gmail users messages list --params '{"userId": "me", "q": "subject:test", "maxResults": 10}'

# Read a message
gws gmail users messages get --params '{"userId": "me", "id": "<MESSAGE_ID>", "format": "full"}'
```

### Calendar

```bash
# List all calendars (includes IDs needed for other calls)
gws calendar calendarList list

# List events
gws calendar events list --params '{"calendarId": "primary", "timeMin": "2026-01-01T00:00:00Z", "maxResults": 10}'

# Create an event
gws calendar events insert \
  --params '{"calendarId": "primary"}' \
  --json '{"summary": "Test", "start": {"dateTime": "2026-04-07T10:00:00-07:00", "timeZone": "America/Los_Angeles"}, "end": {"dateTime": "2026-04-07T10:15:00-07:00", "timeZone": "America/Los_Angeles"}}'

# Delete an event
gws calendar events delete --params '{"calendarId": "primary", "eventId": "<EVENT_ID>"}'
```

---

## Troubleshooting

### 403 "Caller does not have required permission to use project `<project>`"

**Cause:** `~/.config/gws/client_secret.json` references a GCP project that the current user cannot access (e.g. a project created by someone else, or one where the account lacks `serviceusage.services.use`). This file is created by `gws auth setup` as part of normal operation, but becomes a problem if it references an inaccessible project.

**Fix:** Remove the stale client config and any cached token, then re-run setup against a project you do have access to:

```bash
rm -f ~/.config/gws/client_secret.json
rm -f ~/.config/gws/token_cache.json
gcloud config unset project
gws auth setup
```

> Do not delete `~/.config/gws/credentials.enc` — this is the main credential store. Only remove `client_secret.json` and `token_cache.json`.

---

### 403 "requires a quota project, which is not set by default"

**Cause:** You are using Application Default Credentials (ADC) — either `gcloud auth application-default login` was run, or `GOOGLE_WORKSPACE_CLI_TOKEN` is set to a token from `gcloud auth application-default print-access-token`. ADC tokens require a quota project for Drive/Gmail/Calendar.

**Fix:** Revoke ADC and use keyring auth instead:

```bash
gcloud auth application-default revoke --quiet
gws auth setup
```

---

### 401/403 after working previously

**Cause:** Credentials expired or were revoked.

**Fix:**

```bash
gws auth setup
```

---

### Drive works but Gmail/Calendar fail with "insufficient scopes"

**Cause:** You are using `GOOGLE_WORKSPACE_CLI_TOKEN` with a token from `gcloud auth print-access-token`. Even with `--enable-gdrive-access`, `gcloud auth login` only adds the Drive scope to the token — it cannot request Gmail or Calendar scopes. The env var itself is not Drive-only; it accepts any valid token, but the gcloud-derived token lacks the required scopes.

**Fix:** Use `gws auth setup` (keyring), which requests all Workspace scopes during the OAuth flow.

---

### "No OAuth client configured" from gws

**Cause:** No `credentials.enc` or `client_secret.json` exists — `gws auth setup` has never been run on this machine.

**Fix:**

```bash
gcloud auth login
gws auth setup
```

---

## Config File Locations

| File | Purpose |
|---|---|
| `~/.config/gws/credentials.enc` | Primary credential store — encrypted OAuth credentials including refresh token. Do not delete. |
| `~/.config/gws/client_secret.json` | OAuth client config created by `gws auth setup`. Only needed during initial setup; can be safely removed if it references an inaccessible project (credentials.enc holds everything needed for ongoing use). |
| `~/.config/gws/token_cache.json` | Short-lived access token cache. Safe to delete; it will be regenerated on next `gws` command. |
| `~/.config/gcloud/configurations/config_default` | gcloud config. Ensure `project` is not set if it references an inaccessible project: `gcloud config unset project` |
| `~/.config/gcloud/application_default_credentials.json` | ADC credentials. Revoke with `gcloud auth application-default revoke --quiet` if present and causing 403 errors. |

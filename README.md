# hammerhead2garmin

Automatically syncs cycling activities from a [Hammerhead Karoo](https://www.hammerhead.io/) to [Garmin Connect](https://connect.garmin.com/), running daily via GitHub Actions.

> Activities are uploaded as **imports**, not device syncs. Garmin will not re-export them to connected accounts like Strava or Komoot.

## How it works

1. Authenticates with the Hammerhead API using OAuth
2. Fetches activities recorded since the last sync
3. Downloads each activity as a FIT file and uploads it to Garmin Connect
4. Saves sync state to `sync_state.json` so re-runs are always safe

## Prerequisites

- A [Hammerhead developer account](https://support.hammerhead.io/hc/en-us/articles/43558376710683-Creating-a-Developer-Account) with a registered application (to get a Client ID and Client Secret)
- A Garmin Connect account

## Running locally

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env   # fill in your credentials (see below)
uv sync
uv run hammerhead2garmin
```

`.env` variables:

```
HAMMERHEAD_CLIENT_ID=...
HAMMERHEAD_CLIENT_SECRET=...
HAMMERHEAD_USERNAME=your@email.com
HAMMERHEAD_PASSWORD=your_hammerhead_password

GARMIN_USERNAME=your@email.com
GARMIN_PASSWORD=your_garmin_password

# Only sync activities on or after this date (used on first run)
SYNC_FROM_DATE=2026-06-01
```

## Garmin two-factor authentication (MFA)

If your Garmin account has two-factor authentication enabled, the first login
needs an interactive terminal to prompt for the MFA code:

```bash
uv run hammerhead2garmin
# Enter Garmin Connect MFA code: <code from your authenticator/SMS>
```

The resulting session is cached in `garmin_tokens` (override the path with
`GARMIN_TOKENSTORE` in `.env`) and reused on every later run, so MFA is only
needed once — as long as that directory is preserved between runs. This is
not compatible as-is with GitHub Actions, since its filesystem does not
persist across workflow runs; run the first login locally or on your own
server, or disable MFA on the account used for automated syncs.

## Automated daily sync via GitHub Actions

The included workflow runs the sync daily at 20:00 UTC:

1. Fork this repo
2. In the repo create an environment named `garmin-sync` under **Settings → Environments** and add:
   - Secrets: `HAMMERHEAD_CLIENT_ID`, `HAMMERHEAD_CLIENT_SECRET`, `HAMMERHEAD_USERNAME`, `HAMMERHEAD_PASSWORD`, `GARMIN_USERNAME`, `GARMIN_PASSWORD`
   - Variable: `SYNC_FROM_DATE` — the earliest date to sync from in `YYYY-MM-DD` format (e.g. `2026-06-01`), only used on the very first run, then the last sync date is used

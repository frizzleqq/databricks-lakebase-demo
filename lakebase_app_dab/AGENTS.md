# lakebase_bakehouse_viewer

A Databricks App (Streamlit) that reads synced tables from the sibling
`../lakebase_setup_dab` bundle. See README.md for the full rationale,
prerequisites, and the one-time SP grant needed after first deploy.

## For AI Agents

Before touching this app, read:
- `databricks-apps-python` skill (Streamlit framework, app.yaml, deployment)
- `databricks-lakebase` skill, specifically the "Attach Lakebase to an
  existing app" and "Schema Permissions for Deployed Apps" sections

Key things to know:

- This bundle has **no synced tables of its own** — it only reads ones
  created by `../lakebase_setup_dab`. Don't add `postgres_synced_tables`
  or `postgres_projects` resources here; that bundle owns the project.
- The one Lakebase resource this bundle does own is its read-write database
  `app_db` (`resources/app_db.yml`), created inside that same project/branch
  and owned by the setup bundle's `lakebase-owner` role. The app's SP creates
  and owns the `app` schema in it at startup, so it needs no grant. Never
  create that schema under your own credentials (e.g. a local run) — the SP
  would then hit `permission denied`.
- `resources/apps.yml` attaches both databases; the synced one must stay
  first, because `PG*` env vars are only injected for the first database.
- The `postgres` app resource uses `CAN_CONNECT_AND_CREATE`, which does not
  grant access to the pre-existing `sync_bakehouse` schema — run
  `scripts/grant_app_access.py` once after first deploy (see README.md).
  This is expected, not a bug. The app's service principal is always
  auto-created per-app; there's no way to assign a custom SP as its
  runtime identity, which is why this can't be folded into `bundle deploy`.
- `resources/apps.yml` was hand-written against documented field names, not
  generated via `databricks bundle generate app`. If the CLI's actual schema
  has drifted, regenerate from a live deploy rather than guessing further.

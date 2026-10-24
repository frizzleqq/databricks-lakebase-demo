# lakebase_app_dab

Streamlit Databricks App (`bakehouse-lakebase-viewer` in prod, `bakehouse-viewer-<user>` in dev):

- **Synced tables** tab — reads `databricks_postgres.sync_bakehouse.*`, which
  is synced by `../lakebase_setup_dab`.
- **Comments** tab — writes comments on products or customers to `app_db.app.comments`,
  the app's own database in the same Lakebase project.

Requires `../lakebase_setup_dab` to be deployed and seeded. For environments and
the first-deploy order (including the one-time grant), see the [root README](../README.md#environments).

## How the app connects

- Both databases sit on the same Lakebase endpoint. The platform injects
  `PGHOST`/`PGPORT`/`PGUSER`/`PGDATABASE`/`PGSSLMODE` for the **first**
  database resource, which is the synced one. `APP_PGDATABASE` in `app.yaml` names the other.
- There's no `PGPASSWORD`. The app's OAuth token
  (`WorkspaceClient().config.oauth_token()`) is set as the password on each new pooled
  SQLAlchemy connection.
- On first use of the Comments tab, the app creates schema `app` in `app_db`
  and owns it, so it needs no grant there. `sync_bakehouse` belongs to the sync
  pipeline, which is why `scripts/grant_app_access.py` exists.

## Layout

```
databricks.yml               # variables; dev target (forked branch + endpoint) and prod target
resources/
  apps.yml                   # the app + its two database resources
  app_db.yml                 # the app's own database, app_db
scripts/grant_app_access.py  # one-time grants for a new app's SP (synced schema; app schema on forks)
src/app/
  app.py                     # Streamlit UI
  app.yaml                   # run command + env
  requirements.txt           # streamlit>=1.50 (runtime ships 1.38), psycopg2, sqlalchemy, …
```

## Variables

| Variable | dev | prod | Description |
|---|---|---|---|
| `app_name` | `bakehouse-viewer-<user>` | `bakehouse-lakebase-viewer` | App name (max 30 chars) |
| `lakebase_project_id` | `lakebase-bakehouse-demo` | same | Project from `lakebase_setup_dab` |
| `lakebase_branch` | `dev-<user>` | `production` | Branch the app runs against |
| `lakebase_database` | `databricks-postgres` | same | Resource id of the synced database (Postgres name: `databricks_postgres`) |

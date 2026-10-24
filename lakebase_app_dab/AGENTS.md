# lakebase_app_dab — agent notes

Read the root [AGENTS.md](../AGENTS.md) first. Before touching the app, read
the `databricks-apps-python` and `databricks-lakebase` skills. The setup and
workflow are in [../README.md](../README.md).

- The Lakebase project belongs to `../lakebase_setup_dab`. This bundle owns only
  `app_db`, plus the `dev-<user>` branch and its endpoint in the `dev` target.
  Don't add projects or synced tables here.
- There are two targets: `dev` (the default; a forked branch and a per-user app)
  and `prod` (the `production` branch). Pass `-t prod` explicitly for prod.
- `resources/apps.yml`: the synced database must stay the **first** resource,
  because `PG*` env vars are only injected for it.
- `permission denied for schema sync_bakehouse` after a fresh app deploy is
  expected. Run `scripts/grant_app_access.py`; each app gets its own service
  principal, and its id is only known after deploy.
- Don't run the app locally against `app_db` before it has been deployed and
  opened. Your login would own the `app` schema, and the app's service
  principal would then be locked out.

# lakebase_app_dab — agent notes

Read the root [AGENTS.md](../AGENTS.md) first. Before touching the app, read
the `databricks-apps-python` and `databricks-lakebase` skills. The setup,
workflow and gotchas are in [../README.md](../README.md).

- The Lakebase project belongs to `../lakebase_setup_dab`. The only Lakebase
  resource this bundle owns is `app_db`. Don't add projects or synced tables here.
- `resources/apps.yml`: the synced database must stay the **first** resource,
  because `PG*` env vars are only injected for it.
- `permission denied for schema sync_bakehouse` after a fresh app deploy is
  expected. Run `scripts/grant_app_access.py`; each app gets its own service
  principal, and its id is only known after deploy.
- Don't run the app locally against `app_db` before it has been deployed and
  opened. Your login would own the `app` schema, and the app's service
  principal would then be locked out.

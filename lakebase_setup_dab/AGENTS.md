# lakebase_setup_dab — agent notes

Read the root [AGENTS.md](../AGENTS.md) first (it covers the `databricks-core`
skill). Before touching Lakebase resources here, read the `databricks-lakebase` skill,
especially `references/synced-tables.md` and `references/lakehouse-sync.md`. The
setup and workflow are in [../README.md](../README.md).

- Use the `postgres_*` resource family. Never use the deprecated `synced_database_tables`.
- `samples.bakehouse` is read-only. The sync sources are the copies in
  `lake_dev.sync_bakehouse`, created by `seed_source_tables`.
- The database must stay `databricks_postgres`, because Lakehouse Sync only
  supports that database. `../lakebase_app_dab` references it by resource id
  (`databricks-postgres`) and also references the `lakebase-owner` role.
- Always run `bundle plan` before deploying Lakebase changes. Any `delete` or
  `recreate` of a database, catalog or synced table means data loss.
- Synced tables are read-only in Postgres. Keep the reverse-sync demo on its own
  table (`app.franchise_notes`).
- `create-cdf-config` is a real CLI command. It's blocked by the missing external
  storage, which is a platform prerequisite, so don't retry it with other names.

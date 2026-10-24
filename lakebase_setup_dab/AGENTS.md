# Declarative Automation Bundles Project

This project uses Declarative Automation Bundles (DABs) for deployment. Add project-specific instructions below.

## For AI Agents: Use Databricks AI Tools

**BEFORE any other action, read the `databricks-core` skill.**

It sets you up to work with this project reliably: CLI authentication, profile
selection, data discovery, and the bundle deployment workflow. Without it,
results are often slower and less accurate.

If this skill is not available (Databricks AI Tools are not installed), you can install them for your coding agent in seconds:

```bash
databricks aitools install
```

If the CLI is not installed, see: https://docs.databricks.com/dev-tools/cli/install

---

## Project Instructions

**Purpose:** A reduced showcase of Delta → Lakebase sync (and the reverse,
Lakebase → Delta CDC), using `samples.bakehouse` as sample data. Not a
performance-testing project — see `README.md` for the full architecture,
deployment workflow, and reverse-sync walkthrough.

**Before touching Lakebase resources or jobs here**, read the
`databricks-lakebase` skill, specifically `references/synced-tables.md` and
`references/lakehouse-sync.md`.

Key things to know:

- `samples.bakehouse` is read-only — don't try to `ALTER TABLE` it directly.
  The `seed_source_tables` job copies the 3 tables we use into
  `lake_dev.sync_bakehouse` first and enables CDF there; that's the
  actual sync source, not `samples.bakehouse`.
- Lakebase resources use the `postgres_*` DAB resource family
  (`postgres_projects`, `postgres_branches`, `postgres_endpoints`,
  `postgres_roles`, `postgres_databases`, `postgres_catalogs`,
  `postgres_synced_tables`) in `resources/lakebase_sync.yml`.
  Do not use the deprecated `synced_database_tables` resource.
- The database must stay `databricks_postgres` (the default) — Lakehouse Sync
  (the reverse direction) only works for tables in that database. It's
  adopted via `postgres_databases.databricks_postgres` (`replace_existing`) and owned
  by the bundle's `lakebase-owner` role rather than the deployer's personal role.
  `../lakebase_app_dab` references its resource id (`databricks-postgres`).
- Don't drop `create_database_if_missing` from `postgres_catalogs` — it's a
  no-op now, but changing it forces the catalog (and synced tables) to be
  recreated.
- First deploy on a clean workspace can fail creating the synced tables
  because the source tables don't exist yet — run
  `databricks bundle run seed_source_tables`, then `bundle deploy` again. See
  README.md's "Bootstrap ordering note."
- The reverse-sync demo (`scripts/setup_reverse_sync_demo.py`,
  `app.franchise_notes`) deliberately avoids touching the synced tables —
  they're read-only in Postgres (SELECT / CREATE INDEX / DROP TABLE only), and
  Lakehouse Sync's `REPLICA IDENTITY FULL` requirement is not something to
  attempt against a sync-managed table.
- Lakehouse Sync is **not** UI-only — `databricks postgres create-cdf-config`
  is a real CLI command. It's blocked here because no catalog in this
  workspace has external storage (required); that's a platform prerequisite,
  not a tooling gap, so don't retry with different names. See README.md's
  "Reverse sync" section.

## Monorepo layout

This is one of **two independent DAB bundles** living as siblings in the
same repo (`..`), each with its own `databricks.yml`:

- `lakebase_setup_dab/` (this directory) — the sync infrastructure described
  above.
- `../lakebase_app_dab/` — a separate Streamlit Databricks App that reads
  the synced tables. Has its own prerequisites and a one-time service
  principal grant; see its README.md and AGENTS.md before touching it.

Deploy each bundle from its own directory — don't merge them into one
`bundle deploy`; that would compound this bundle's existing
bootstrap-ordering issue with the app's own.

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
  `postgres_catalogs`, `postgres_synced_tables`) in `resources/lakebase_sync.yml`.
  Do not use the deprecated `synced_database_tables` resource.
- `postgres_catalogs.postgres_database` must stay `databricks_postgres` (the
  default) — Lakehouse Sync (the reverse direction) only works for tables in
  that database.
- First deploy on a clean workspace can fail creating the synced tables
  because the source tables don't exist yet — run
  `databricks bundle run seed_source_tables`, then `bundle deploy` again. See
  README.md's "Bootstrap ordering note."
- The reverse-sync demo (`scripts/setup_reverse_sync_demo.py`,
  `public.franchise_notes`) deliberately avoids touching the synced tables —
  they're read-only in Postgres (SELECT / CREATE INDEX / DROP TABLE only), and
  Lakehouse Sync's `REPLICA IDENTITY FULL` requirement is not something to
  attempt against a sync-managed table.
- Lakehouse Sync enablement itself is UI-only (no CLI/API) — never try to
  automate or script around that; just point the user at the manual step in
  README.md.

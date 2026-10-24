# databricks_lakebase

A small showcase of Lakebase (Databricks' managed Postgres): Delta tables are
synced into Lakebase, and a Databricks App reads them and writes its own data
to a separate database in the same Lakebase project. Sample data comes from
`samples.bakehouse`.

## Architecture

```
Unity Catalog (lake_dev.sync_bakehouse)          Lakebase project: lakebase-bakehouse-demo / branch: production
───────────────────────────────────────          ──────────────────────────────────────────────────────────────
sales_franchises    ──SNAPSHOT──►  db databricks_postgres                     db app_db
sales_customers     ──TRIGGERED─►    schema sync_bakehouse (synced, RO)         schema app (owned by the app)
sales_transactions  ──TRIGGERED─►      3 tables                ──read──┐          comments  ◄──write──┐
                                                                       └──── Databricks App ──────────┘
                                                                          bakehouse-lakebase-viewer
```

Two independent bundles, each deployed from its own directory:

| Bundle | Owns |
|---|---|
| [`lakebase_setup_dab/`](lakebase_setup_dab/README.md) | UC schema + seed jobs, the Lakebase project/branch/endpoint, the `lakebase-owner` role, the `databricks_postgres` database, its UC catalog and the 3 synced tables |
| [`lakebase_app_dab/`](lakebase_app_dab/README.md) | The Streamlit app and its own `app_db` database (created inside the setup bundle's project) |

They're kept separate because each has its own first-deploy ordering step
(see [Workflow](#workflow)); a single `bundle deploy` would combine both.

## Permissions model

| Who | Where | What | How |
|---|---|---|---|
| `lakebase-owner` role | `databricks_postgres`, `app_db` | Database owner | `postgres_roles` / `postgres_databases` — not tied to the deployer's identity |
| Sync pipeline | `sync_bakehouse.*` | Owns and writes the synced tables | Created by `postgres_synced_tables` |
| App service principal | `sync_bakehouse.*` | `USAGE` + `SELECT` only | One-time `scripts/grant_app_access.py` |
| App service principal | `app_db` | `CONNECT` + `CREATE`; owns schema `app` | App resource `CAN_CONNECT_AND_CREATE`; app creates the schema on startup |
| `group_etl` | Project, UC schema, app | `CAN_USE`, `USE_SCHEMA`+`SELECT`, `CAN_USE` | Showcase grants in the YAML |

Synced tables are read-only in Postgres anyway (only `SELECT`, `CREATE INDEX`,
`DROP TABLE`); writing to them would break the sync.

## Prerequisites

- Databricks CLI ≥ v0.294.0 and [`uv`](https://docs.astral.sh/uv/).
- A CLI profile for the workspace. Commands below use `<PROFILE>` as a
  placeholder — use whatever you named yours (`databricks auth profiles`).
  Use OAuth; `databricks apps logs` doesn't work with a PAT:

  ```bash
  databricks auth login --host https://dbc-ea4bb8e5-6935.cloud.databricks.com --profile <PROFILE>
  ```

## Workflow

### First deploy

```bash
# 1. Sync infrastructure
cd lakebase_setup_dab
databricks bundle deploy --profile <PROFILE>               # synced tables may fail: sources don't exist yet
databricks bundle run seed_source_tables --profile <PROFILE>
databricks bundle deploy --profile <PROFILE>               # now creates the synced tables

# 2. App (creates app_db and the app's service principal)
cd ../lakebase_app_dab
databricks bundle deploy --profile <PROFILE>
databricks bundle run bakehouse_viewer --profile <PROFILE>

# 3. Let the app's service principal read the synced schema (run from lakebase_setup_dab for its venv)
cd ../lakebase_setup_dab
uv run python ../lakebase_app_dab/scripts/grant_app_access.py \
  --profile <PROFILE> --project-id lakebase-bakehouse-demo --app-name bakehouse-lakebase-viewer
```

Open the app via `databricks apps get bakehouse-lakebase-viewer --profile <PROFILE>` (→ `url`).
Repeat step 3 if the app is ever deleted and recreated — it gets a new service principal.

### Day to day

```bash
# In lakebase_setup_dab: change source rows, then push them to Lakebase
databricks bundle run simulate_changes --profile <PROFILE>
databricks bundle run trigger_lakebase_sync --profile <PROFILE>
uv run python scripts/check_lakebase.py --profile <PROFILE> --project-id lakebase-bakehouse-demo

# In lakebase_app_dab: ship app changes and check them
databricks bundle deploy --profile <PROFILE> && databricks bundle run bakehouse_viewer --profile <PROFILE>
databricks apps logs bakehouse-lakebase-viewer --profile <PROFILE>
```

Run `databricks bundle plan --profile <PROFILE>` before deploying any change to
Lakebase resources — see the gotchas below.

### Cleanup

Destroy the app first; `app_db` lives inside the setup bundle's project.

```bash
cd lakebase_app_dab   && databricks bundle destroy --profile <PROFILE>
cd ../lakebase_setup_dab && databricks bundle destroy --profile <PROFILE>
# Projects are soft-deleted for 7 days; to free the id immediately:
databricks postgres delete-project projects/lakebase-bakehouse-demo --purge --profile <PROFILE>
```

## Gotchas

- **Resource id ≠ Postgres name.** Databases have a hyphenated resource id
  (`databricks-postgres`, `app-db`, used in API paths) and an underscored
  Postgres name (`databricks_postgres`, `app_db`, used to connect).
- **Renaming a Lakebase resource key deletes and recreates it.** For a
  database that means data loss. Instead: `databricks bundle deployment unbind <old_key>`
  (with the old key still in the YAML), rename, then deploy — `replace_existing: true`
  adopts the existing resource.
- **Don't remove `create_database_if_missing`** from the `postgres_catalogs`
  resource — changing it recreates the catalog and its synced tables.
- **Never create the app's `app` schema under your own login** (e.g. running
  the app locally first). Your role would own it and the app would get
  `permission denied`.
- **Only the first database in the app's `resources:` gets `PG*` env vars.**
  The synced one stays first; `app_db` is selected via `APP_PGDATABASE`.
- **Reverse sync (Lakebase → Delta) is blocked in this workspace** — it needs
  a catalog on external storage. See
  [lakebase_setup_dab/README.md](lakebase_setup_dab/README.md#reverse-sync-lakebase--delta).

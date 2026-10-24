# lakebase_setup_dab

Syncs three `samples.bakehouse` tables from Delta into Lakebase Postgres, and
sketches the reverse direction (Lakebase → Delta CDC). For the overall setup,
first-deploy order and cleanup, see the [root README](../README.md).

## Data flow

`samples.bakehouse` is read-only, so Change Data Feed can't be enabled on it.
The `seed_source_tables` job copies the tables into `lake_dev.sync_bakehouse`
and enables CDF there; those copies are the sync sources.

| Table | Sync mode | Why |
|---|---|---|
| `sales_franchises` | `SNAPSHOT` (no CDF) | Small reference table — full copy each run |
| `sales_customers` | `TRIGGERED` | Incremental sync via CDF |
| `sales_transactions` | `TRIGGERED` | Pairs with `simulate_changes` to show new rows flowing through |

They land in `databricks_postgres.sync_bakehouse` in Lakebase, and are also
browsable in UC under the `lakebase-bakehouse-demo` catalog.

## Layout

```
databricks.yml               # variables, dev target
resources/
  schemas.yml                # UC schema sync_bakehouse
  lakebase_sync.yml          # project, branch, endpoint, owner role, database, catalog, synced tables
  jobs.yml                   # seed_source_tables, simulate_changes, trigger_lakebase_sync
src/notebooks/               # the three job notebooks
scripts/
  check_lakebase.py          # prints row counts straight from Postgres
  setup_reverse_sync_demo.py # creates app.franchise_notes for the reverse demo
```

## Variables

| Variable | prod value | Description |
|---|---|---|
| `catalog` | `lake_dev` | UC catalog for the Delta sources and pipeline storage |
| `schema` | `sync_bakehouse` | UC schema and matching Postgres schema |
| `lakebase_project_id` | `lakebase-bakehouse-demo` | Lakebase project id, also the UC catalog name |

## Querying Postgres directly

```bash
uv run python scripts/check_lakebase.py --profile <PROFILE> --project-id lakebase-bakehouse-demo
# or, with psql installed:
databricks psql --project lakebase-bakehouse-demo --profile <PROFILE>
```

## Reverse sync (Lakebase → Delta)

`databricks postgres create-cdf-config` streams changes from Postgres tables
into a Delta history table. It can't target synced tables, so the demo uses a
plain table, `app.franchise_notes`, which must live in `databricks_postgres`.

```bash
uv run python scripts/setup_reverse_sync_demo.py --profile <PROFILE> --project-id lakebase-bakehouse-demo

databricks postgres create-cdf-config \
  projects/lakebase-bakehouse-demo/branches/production/databases/databricks-postgres \
  <destination_catalog> <destination_schema> app \
  --cdf-config-id app_to_delta --profile <PROFILE>
```

**Blocked in this workspace:** `Lakebase CDF is not supported for catalogs
using Default Storage`. It needs a catalog on an external storage location,
and none exists here. Once set up, it creates
`<destination_catalog>.<destination_schema>.lb_franchise_notes_history`:

```sql
-- Latest state of each row
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY _pg_lsn DESC) AS rn
  FROM <destination_catalog>.<destination_schema>.lb_franchise_notes_history
  WHERE _pg_change_type IN ('insert', 'update_postimage', 'delete')
)
WHERE rn = 1 AND _pg_change_type != 'delete';
```

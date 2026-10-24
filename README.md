# databricks_lakebase

A reduced, teaching-oriented Databricks Asset Bundle (DAB) that shows how to sync
Delta tables into Lakebase Autoscaling Postgres, and how the reverse direction
(Lakebase -> Delta via CDC) works. Uses `samples.bakehouse` as sample data —
this is a showcase, not a performance test.

## What this bundle does

1. **Creates a Lakebase Autoscaling project** with a managed production branch and
   primary read-write endpoint (0.5 CU — showcase sizing).
2. **Binds the project's production branch as a Unity Catalog catalog** via `postgres_catalogs`.
3. **Creates 3 synced tables** in the `sync_bakehouse` schema — two in `TRIGGERED`
   (incremental, Change Data Feed) mode, one in `SNAPSHOT` mode.
4. **Triggers refreshes** on demand via a Python job that calls the Lakeflow pipeline
   backing each synced table.
5. Documents the **reverse direction**: a plain Postgres table written to
   directly, synced back into Delta as CDC history via Lakehouse Sync
   (`databricks postgres create-cdf-config`) — blocked in this workspace by a
   platform prerequisite, not automation. See [Reverse sync](#reverse-sync-lakebase--delta).

## Architecture

```
samples.bakehouse (read-only)              Our own schema (CDF-enabled copies)        Lakebase (PostgreSQL)
──────────────────────────────             ────────────────────────────────────       ─────────────────────
sales_franchises     ──(CTAS, seed job)──► lake_dev.sync_bakehouse.    ──────► <project>.sync_bakehouse.
                                            sales_franchises  [no CDF]  SNAPSHOT        sales_franchises

sales_customers      ──(CTAS, seed job)──► lake_dev.sync_bakehouse.    ──────► <project>.sync_bakehouse.
                                            sales_customers   [CDF on]  TRIGGERED       sales_customers

sales_transactions   ──(CTAS, seed job)──► lake_dev.sync_bakehouse.    ──────► <project>.sync_bakehouse.
                                            sales_transactions [CDF on] TRIGGERED       sales_transactions
```

`samples.bakehouse` is a read-only system catalog, so we can't enable Change Data
Feed on it directly (required for `TRIGGERED`/`CONTINUOUS` sync). The `seed_source_tables`
job copies the 3 tables we care about into our own `sync_bakehouse` schema first,
enables CDF on the two that sync incrementally, and those copies become the actual
sync sources.

Reverse direction (Lakebase -> Delta CDC), see [Reverse sync](#reverse-sync-lakebase--delta) below:

```
Lakebase (app.franchise_notes, written to directly)  ──(create-cdf-config, blocked here)──►  <externally-backed catalog>.<schema>.lb_franchise_notes_history
```

## Project layout

```
databricks.yml                       # bundle root — variables, targets
resources/
  schemas.yml                        # UC schema: sync_bakehouse
  lakebase_sync.yml                  # Lakebase project/branch/endpoint/catalog + 3 synced tables
  jobs.yml                           # seed_source_tables, simulate_changes, trigger_lakebase_sync
src/
  notebooks/
    seed_source_tables.py            # CTAS copies from samples.bakehouse; enables CDF
    simulate_changes.py              # inserts/updates rows so TRIGGERED sync has real CDF changes
    trigger_lakebase_sync.py         # triggers a refresh on each synced table's pipeline
scripts/
  check_lakebase.py                  # connects to Postgres directly, prints row counts
  setup_reverse_sync_demo.py         # creates the native franchise_notes table for the reverse demo
```

## Variables

| Variable | dev default | prod default | Description |
|---|---|---|---|
| `catalog` | `lake_dev` | `lake_dev` | UC catalog for the source Delta tables and pipeline checkpoint storage |
| `schema` | `sync_bakehouse` | `sync_bakehouse` | UC schema (and matching Postgres schema) for the synced tables |
| `lakebase_project_id` | `lakebase-bakehouse-demo` | `lakebase-bakehouse-prod` | Lakebase project id (also the destination UC catalog name) |

## Prerequisites

- Databricks CLI with support for `postgres_projects` / `postgres_branches` / `postgres_endpoints` / `postgres_catalogs` / `postgres_synced_tables` DAB resource types
- `uv` installed (`uv sync --dev` for local dependencies)
- Workspace: `https://dbc-ea4bb8e5-6935.cloud.databricks.com` (profile `personal`)

## Deployment

```bash
# Authenticate (once)
databricks configure --profile personal

# Validate
databricks bundle validate --profile personal

# Deploy
databricks bundle deploy --profile personal
```

> **Bootstrap ordering note:** `postgres_synced_tables` resources reference
> `source_table_full_name`, which should exist for Terraform to create them cleanly.
> On a brand-new deployment the source tables don't exist yet. If `bundle deploy`
> reports a problem creating the synced tables, that's expected on the very first
> deploy — run the seed job below, then deploy again:
>
> ```bash
> databricks bundle run seed_source_tables --profile personal
> databricks bundle deploy --profile personal
> ```

Once deployed and seeded:

```bash
# Simulate some new/changed rows, then trigger an incremental refresh
databricks bundle run simulate_changes --profile personal
databricks bundle run trigger_lakebase_sync --profile personal

# Check sync status
databricks postgres get-synced-table "synced_tables/<project_id>.sync_bakehouse.sales_customers" --profile personal
```

`bundle deploy` is idempotent — safe to re-run.

## Querying the PostgreSQL database directly

```python
from databricks.sdk import WorkspaceClient
import psycopg

w = WorkspaceClient(profile="personal")
project_id = "lakebase-bakehouse-demo"
branch = f"projects/{project_id}/branches/production"

host = next(iter(w.postgres.list_endpoints(parent=branch))).status.hosts.host
cred = w.postgres.generate_database_credential(endpoint=f"{branch}/endpoints/primary")

conn = psycopg.connect(
    host=host, port=5432, dbname="databricks_postgres",
    user=w.current_user.me().user_name, password=cred.token, sslmode="require",
)
cur = conn.cursor()
cur.execute("SELECT count(*) FROM sync_bakehouse.sales_customers")
print(cur.fetchone())
```

See `scripts/check_lakebase.py` for a full example across all 3 tables:

```bash
uv run python scripts/check_lakebase.py --profile personal --project-id lakebase-bakehouse-demo
```

## Sync modes used here

| Table | Mode | Why |
|---|---|---|
| `sales_franchises` | `SNAPSHOT` | Small reference table — full copy each run is simplest and cheap |
| `sales_customers` | `TRIGGERED` | Demonstrates incremental sync via Change Data Feed |
| `sales_transactions` | `TRIGGERED` | Fact-table-style data; pairs with `simulate_changes` to show new rows flowing through |

## Reverse sync (Lakebase → Delta)

`databricks postgres create-cdf-config` streams Postgres changes into a Delta
CDC table — a real CLI command, not UI-only. It can't target a *synced* table
(read-only), so this demo uses one plain table, `app.franchise_notes`.

```bash
uv run python scripts/setup_reverse_sync_demo.py --profile personal --project-id lakebase-bakehouse-demo

databricks postgres create-cdf-config \
  "projects/lakebase-bakehouse-demo/branches/production/databases/databricks-postgres" \
  <destination_catalog> <destination_schema> app \
  --cdf-config-id app_to_delta --profile personal
```

**Blocked in this workspace:** `Lakebase CDF is not supported for catalogs
using Default Storage` — every catalog here uses default metastore storage,
and this requires one backed by an external storage location (none exist).
Needs real external storage set up first (storage credential + external
location + a catalog on it); not something to provision inside this demo.
Once available, it creates `<destination_catalog>.<destination_schema>.lb_franchise_notes_history`.

**3. Query the history table:**

Latest state of each row:

```sql
SELECT *
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY id ORDER BY _pg_lsn DESC) AS rn
  FROM lake_dev.sync_bakehouse.lb_franchise_notes_history
  WHERE _pg_change_type IN ('insert', 'update_postimage', 'delete')
)
WHERE rn = 1 AND _pg_change_type != 'delete';
```

Full change history for a note:

```sql
SELECT *
FROM lake_dev.sync_bakehouse.lb_franchise_notes_history
WHERE id = 1
ORDER BY _pg_lsn;
```

## Cleanup

```bash
databricks bundle destroy --profile personal
# Postgres projects have a 7-day soft-delete retention; to free the project id immediately:
databricks postgres delete-project "projects/lakebase-bakehouse-demo" --purge --profile personal
```

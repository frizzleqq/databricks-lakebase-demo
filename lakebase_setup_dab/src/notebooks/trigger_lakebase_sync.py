# Databricks notebook source
# Triggers an incremental refresh of each Lakebase synced table.
# The postgres SDK client has no direct "refresh" call -- a refresh is done
# by finding the Lakeflow pipeline backing each synced table and starting an
# incremental update on it. Pattern adapted from the paiqo/databricks_lakebase
# reference project's lakebase_sync_trigger.py.

# COMMAND ----------
dbutils.widgets.text("lakebase_catalog", "")
dbutils.widgets.text("schema", "sync_bakehouse")

lakebase_catalog = dbutils.widgets.get("lakebase_catalog")
schema = dbutils.widgets.get("schema")

TABLES = ["sales_franchises", "sales_customers", "sales_transactions"]

# COMMAND ----------
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()


def _get_pipeline_id(synced_table_name: str) -> str:
    table = w.postgres.get_synced_table(f"synced_tables/{synced_table_name}")
    pipeline_id = table.status.pipeline_id if table.status else None
    if not pipeline_id:
        raise RuntimeError(f"No pipeline_id found for {synced_table_name}")
    return pipeline_id


def _trigger_pipeline(pipeline_id: str) -> None:
    try:
        w.pipelines.start_update(pipeline_id=pipeline_id, full_refresh=False)
        print(f"Refresh triggered: pipeline {pipeline_id}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"Skipped (update already running): pipeline {pipeline_id}")
        else:
            raise


# COMMAND ----------
seen = set()
for table in TABLES:
    synced_table_name = f"{lakebase_catalog}.{schema}.{table}"
    pipeline_id = _get_pipeline_id(synced_table_name)
    if pipeline_id in seen:
        print(f"Skipped (same pipeline already triggered): {synced_table_name}")
        continue
    seen.add(pipeline_id)
    _trigger_pipeline(pipeline_id)

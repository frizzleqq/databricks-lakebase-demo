# Databricks notebook source
# Copies 3 tables from the read-only samples.bakehouse catalog into our own
# schema, so we have Delta tables we're allowed to enable Change Data Feed
# (CDF) on. ALTER TABLE on samples.bakehouse itself would fail -- it's a
# system catalog we don't own.
#
# Runs during `bundle deploy` (the initial_seed job run), so it is idempotent:
# existing tables are left alone, keeping simulated changes and the CDF history
# the TRIGGERED syncs rely on. Drop a table to have it re-seeded.

# COMMAND ----------
dbutils.widgets.text("catalog", "lake_dev")
dbutils.widgets.text("schema", "sync_bakehouse")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------
# sales_franchises is synced in SNAPSHOT mode -- no CDF needed.
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{schema}.sales_franchises
    AS SELECT * FROM samples.bakehouse.sales_franchises
""")

# COMMAND ----------
# sales_customers and sales_transactions are synced in TRIGGERED mode, which
# needs Change Data Feed enabled on the source table.
for table in ["sales_customers", "sales_transactions"]:
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table}
        AS SELECT * FROM samples.bakehouse.{table}
    """)
    spark.sql(f"""
        ALTER TABLE {catalog}.{schema}.{table}
        SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
    """)

# COMMAND ----------
for table in ["sales_franchises", "sales_customers", "sales_transactions"]:
    count = spark.table(f"{catalog}.{schema}.{table}").count()
    print(f"{catalog}.{schema}.{table}: {count} rows")

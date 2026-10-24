import os

import pandas as pd
import psycopg2
import streamlit as st
from databricks.sdk import WorkspaceClient

SCHEMA = os.getenv("LAKEBASE_SCHEMA", "sync_bakehouse")
TABLES = ["sales_franchises", "sales_customers", "sales_transactions"]

st.set_page_config(page_title="Bakehouse Lakebase Viewer", layout="wide")


@st.cache_resource
def get_workspace_client() -> WorkspaceClient:
    return WorkspaceClient()


def get_connection():
    # The `postgres` app resource only auto-injects PGHOST/PGPORT/PGDATABASE/
    # PGUSER/PGSSLMODE -- no PGPASSWORD. LAKEBASE_ENDPOINT comes from
    # `valueFrom: postgres` in app.yaml. Mint a short-lived OAuth token per
    # connection instead (tokens expire, so don't cache this).
    w = get_workspace_client()
    token = w.postgres.generate_database_credential(endpoint=os.environ["LAKEBASE_ENDPOINT"]).token
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=token,
        port=os.environ.get("PGPORT", "5432"),
        sslmode=os.environ.get("PGSSLMODE", "require"),
    )


def load_table(table: str, limit: int) -> tuple[pd.DataFrame, int]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{table}")
            total = cur.fetchone()[0]
        df = pd.read_sql(f"SELECT * FROM {SCHEMA}.{table} LIMIT %s", conn, params=(limit,))
    finally:
        conn.close()
    return df, total


st.title("Bakehouse Lakebase Viewer")
st.caption(f"Synced tables in schema `{SCHEMA}` — written by Lakehouse Sync, read-only here.")

table = st.selectbox("Synced table", TABLES)
limit = st.slider("Rows to preview", 10, 500, 100)

try:
    df, total = load_table(table, limit)
    st.metric("Total rows", total)
    st.dataframe(df, width="stretch")
except Exception as exc:  # surfaced in the UI rather than a bare 500
    st.error(f"Query failed: {exc}")
    st.info(
        "If this is `permission denied for schema`, the app's service "
        "principal hasn't been granted access yet — see README.md."
    )

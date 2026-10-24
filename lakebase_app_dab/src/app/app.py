import os

import pandas as pd
import psycopg2
import streamlit as st

SCHEMA = os.getenv("LAKEBASE_SCHEMA", "sync_bakehouse")
TABLES = ["sales_franchises", "sales_customers", "sales_transactions"]

st.set_page_config(page_title="Bakehouse Lakebase Viewer", layout="wide")


@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        port=os.environ.get("PGPORT", "5432"),
        sslmode="require",
    )


def load_table(table: str, limit: int) -> tuple[pd.DataFrame, int]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{table}")
        total = cur.fetchone()[0]
    df = pd.read_sql(f"SELECT * FROM {SCHEMA}.{table} LIMIT %s", conn, params=(limit,))
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

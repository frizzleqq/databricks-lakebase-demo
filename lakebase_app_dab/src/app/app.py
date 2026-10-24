import os

import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient
from sqlalchemy import URL, Engine, create_engine, event, text

SCHEMA = os.getenv("LAKEBASE_SCHEMA", "sync_bakehouse")
TABLES = ["sales_franchises", "sales_customers", "sales_transactions"]

st.set_page_config(page_title="Bakehouse Lakebase Viewer", layout="wide")


@st.cache_resource
def get_engine() -> Engine:
    # The `postgres` app resource auto-injects PGHOST/PGPORT/PGDATABASE/PGUSER/
    # PGSSLMODE -- no PGPASSWORD. The app's own OAuth token is the password;
    # it's only checked at login, so set it per new pooled connection.
    w = WorkspaceClient()
    engine = create_engine(
        URL.create(
            "postgresql+psycopg2",
            username=os.environ["PGUSER"],
            host=os.environ["PGHOST"],
            port=int(os.environ.get("PGPORT", "5432")),
            database=os.environ["PGDATABASE"],
        ),
        connect_args={"sslmode": os.environ.get("PGSSLMODE", "require")},
        pool_pre_ping=True,  # compute may have scaled to zero since last use
    )

    @event.listens_for(engine, "do_connect")
    def provide_token(dialect, conn_rec, cargs, cparams):
        cparams["password"] = w.config.oauth_token().access_token

    return engine


def load_table(table: str, limit: int) -> tuple[pd.DataFrame, int]:
    with get_engine().connect() as conn:
        total = conn.execute(text(f"SELECT COUNT(*) FROM {SCHEMA}.{table}")).scalar_one()
        df = pd.read_sql(text(f"SELECT * FROM {SCHEMA}.{table} LIMIT :limit"), conn, params={"limit": limit})
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

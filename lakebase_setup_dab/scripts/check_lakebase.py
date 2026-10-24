"""Verify the Delta -> Lakebase sync by querying Postgres directly.

Usage:
    uv run python scripts/check_lakebase.py --profile personal --project-id lakebase-bakehouse-<user>
"""

import argparse

import psycopg
from databricks.sdk import WorkspaceClient

SCHEMA = "sync_bakehouse"
SYNCED_TABLES = ["sales_franchises", "sales_customers", "sales_transactions"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="Databricks CLI profile")
    parser.add_argument("--project-id", required=True, help="Lakebase project id (var.lakebase_project_id)")
    args = parser.parse_args()

    w = WorkspaceClient(profile=args.profile)
    branch = f"projects/{args.project_id}/branches/production"
    endpoint = f"{branch}/endpoints/primary"

    host = next(iter(w.postgres.list_endpoints(parent=branch))).status.hosts.host
    user = w.current_user.me().user_name
    cred = w.postgres.generate_database_credential(endpoint=endpoint)

    conn = psycopg.connect(
        host=host,
        port=5432,
        dbname="databricks_postgres",
        user=user,
        password=cred.token,
        sslmode="require",
    )

    with conn, conn.cursor() as cur:
        print(f"Connected to {host} as {user}\n")

        for table in SYNCED_TABLES:
            cur.execute(f"SELECT count(*) FROM {SCHEMA}.{table}")
            print(f"{SCHEMA}.{table}: {cur.fetchone()[0]} rows")

        cur.execute("SELECT to_regclass('app.franchise_notes')")
        if cur.fetchone()[0] is not None:
            cur.execute("SELECT count(*) FROM app.franchise_notes")
            print(f"app.franchise_notes: {cur.fetchone()[0]} rows")
        else:
            print("app.franchise_notes: not created yet (run scripts/setup_reverse_sync_demo.py)")


if __name__ == "__main__":
    main()

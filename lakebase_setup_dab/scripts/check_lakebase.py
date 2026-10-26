"""Verify the Delta -> Lakebase sync by querying Postgres directly.

Usage:
    uv run python scripts/check_lakebase.py --project-id lakebase-bakehouse-<user>
"""

import argparse
from pathlib import Path

import psycopg
import yaml
from databricks.sdk import WorkspaceClient

SCHEMA = "sync_bakehouse"
SYNCED_TABLES = ["sales_franchises", "sales_customers", "sales_transactions"]
LOCAL_CONFIG = Path(__file__).resolve().parents[2] / "databricks.local.yml"


def workspace_client(profile: str | None) -> WorkspaceClient:
    """Use --profile if given, else the workspace from the repo's databricks.local.yml."""
    if profile:
        return WorkspaceClient(profile=profile)
    if not LOCAL_CONFIG.exists():
        raise SystemExit(f"{LOCAL_CONFIG} not found: copy databricks.local.yml.example, or pass --profile.")
    workspace = yaml.safe_load(LOCAL_CONFIG.read_text())["workspace"]
    return WorkspaceClient(host=workspace["host"], profile=workspace.get("profile"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Databricks CLI profile (default: ../databricks.local.yml)")
    parser.add_argument("--project-id", required=True, help="Lakebase project id (var.lakebase_project_id)")
    args = parser.parse_args()

    w = workspace_client(args.profile)
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


if __name__ == "__main__":
    main()

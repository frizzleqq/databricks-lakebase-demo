"""Set up the reverse-direction (Lakebase -> Delta) sync demo.

Creates a plain, directly-written Postgres table in Lakebase -- NOT a Lakebase
synced table, which is read-only (SELECT / CREATE INDEX / DROP TABLE only) and
not a safe target for the REPLICA IDENTITY change Lakehouse Sync requires.
This table simulates rows an application would write straight into Lakebase.

After running this script, enable Lakehouse Sync with
`databricks postgres create-cdf-config` (a real CLI command, not UI-only).
Currently blocked here -- no catalog in this workspace has external storage,
which this requires. See README.md's "Reverse sync" section.

Usage:
    uv run python scripts/setup_reverse_sync_demo.py --profile personal --project-id lakebase-bakehouse-<user>
"""

import argparse

import psycopg
from databricks.sdk import WorkspaceClient

SAMPLE_NOTES = [
    (1, "Ovens serviced ahead of the holiday rush."),
    (2, "New espresso machine installed."),
    (3, "Customer praised the sourdough restock."),
    (5, "Short-staffed on weekends, hiring in progress."),
    (8, "Local supplier swap for flour starting next month."),
]


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
        cur.execute("CREATE SCHEMA IF NOT EXISTS app")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS app.franchise_notes (
                id SERIAL PRIMARY KEY,
                franchise_id BIGINT NOT NULL,
                note TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)

        cur.executemany(
            "INSERT INTO app.franchise_notes (franchise_id, note) VALUES (%s, %s)",
            SAMPLE_NOTES,
        )

        # Required by Lakehouse Sync so it can capture full before/after row
        # images for updates and deletes, not just the primary key.
        cur.execute("ALTER TABLE app.franchise_notes REPLICA IDENTITY FULL")

        conn.commit()

        cur.execute("SELECT count(*) FROM app.franchise_notes")
        print(f"app.franchise_notes ready with {cur.fetchone()[0]} rows, REPLICA IDENTITY FULL set.")
        print("Next: enable Lakehouse Sync for this table from the workspace UI (see README.md).")


if __name__ == "__main__":
    main()

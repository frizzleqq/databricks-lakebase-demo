"""Grant a deployed app's service principal access it can't get on its own.

- SELECT on the synced schema in databricks_postgres (owned by the sync pipeline).
- On a forked branch (e.g. dev): access to the `app` schema in app_db, which
  the fork copied over still owned by the source branch's app (e.g. prod's).

Each app gets its own service principal, known only after deploy, so run this
once per app/branch after its first deploy. Run from ../lakebase_setup_dab for
its venv (databricks-sdk, psycopg), as the Lakebase project owner:

    cd ../lakebase_setup_dab
    uv run python ../lakebase_app_dab/scripts/grant_app_access.py \
        --project-id lakebase-bakehouse-demo \
        --app-name <APP_NAME> [--branch <BRANCH>]
"""

import argparse
from pathlib import Path

import psycopg
import yaml
from databricks.sdk import WorkspaceClient

SCHEMA = "sync_bakehouse"
APP_DB = "app_db"
APP_SCHEMA = "app"
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
    parser.add_argument("--project-id", required=True, help="Lakebase project id owning the synced tables")
    parser.add_argument("--app-name", required=True, help="Deployed app name (resources.apps.<key>.name)")
    parser.add_argument("--branch", default="production")
    args = parser.parse_args()

    w = workspace_client(args.profile)

    app = w.apps.get(name=args.app_name)
    client_id = app.service_principal_client_id
    if not client_id:
        raise SystemExit(f"App {args.app_name!r} has no service_principal_client_id yet — deploy it first.")

    branch = f"projects/{args.project_id}/branches/{args.branch}"
    endpoint = f"{branch}/endpoints/primary"
    host = next(iter(w.postgres.list_endpoints(parent=branch))).status.hosts.host
    user = w.current_user.me().user_name
    cred = w.postgres.generate_database_credential(endpoint=endpoint)

    def connect(dbname: str) -> psycopg.Connection:
        return psycopg.connect(host=host, port=5432, dbname=dbname, user=user, password=cred.token, sslmode="require")

    with connect("databricks_postgres") as conn, conn.cursor() as cur:
        cur.execute(f'GRANT USAGE ON SCHEMA {SCHEMA} TO "{client_id}"')
        cur.execute(f'GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO "{client_id}"')
        cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {SCHEMA} GRANT SELECT ON TABLES TO "{client_id}"')
    print(f"Granted SELECT on {SCHEMA}.* to app SP {client_id} ({args.app_name})")

    with connect(APP_DB) as conn, conn.cursor() as cur:
        cur.execute("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = %s", (APP_SCHEMA,))
        row = cur.fetchone()
        if row is None or row[0] == client_id:
            return  # app creates (or already owns) the schema itself
        cur.execute(f'GRANT USAGE, CREATE ON SCHEMA {APP_SCHEMA} TO "{client_id}"')
        # No sequence grant: the project owner can't grant on sequences owned by
        # another role, which is why app.comments uses an IDENTITY id.
        cur.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {APP_SCHEMA} TO "{client_id}"')
    print(f"Granted access to {APP_DB}.{APP_SCHEMA} (owned by {row[0]}) to app SP {client_id}")


if __name__ == "__main__":
    main()

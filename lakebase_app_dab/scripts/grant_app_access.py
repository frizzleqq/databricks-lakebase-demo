"""Grant the deployed app's service principal SELECT on the synced schema.

Each Databricks App gets its own auto-created service principal — its
client id isn't known until the app resource exists, so this can't be
baked into `bundle deploy` itself. Run this once after the app's first
deploy (and again if the app is ever recreated).

Run from ../lakebase_setup_dab so it picks up that bundle's venv
(databricks-sdk, psycopg are declared in its pyproject.toml):

    cd ../lakebase_setup_dab
    uv run python ../lakebase_app_dab/scripts/grant_app_access.py \
        --profile <PROFILE> --project-id lakebase-bakehouse-demo \
        --app-name bakehouse-lakebase-viewer

Must be run as a principal with GRANT privileges on the schema — e.g. the
Lakebase project owner (default for whoever created the project).
"""

import argparse

import psycopg
from databricks.sdk import WorkspaceClient

SCHEMA = "sync_bakehouse"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="Databricks CLI profile")
    parser.add_argument("--project-id", required=True, help="Lakebase project id owning the synced tables")
    parser.add_argument("--app-name", required=True, help="Deployed app name (resources.apps.<key>.name)")
    parser.add_argument("--branch", default="production")
    args = parser.parse_args()

    w = WorkspaceClient(profile=args.profile)

    app = w.apps.get(name=args.app_name)
    client_id = app.service_principal_client_id
    if not client_id:
        raise SystemExit(
            f"App {args.app_name!r} has no service_principal_client_id yet — "
            "deploy it first (`databricks bundle deploy` from apps/bakehouse_viewer)."
        )

    branch = f"projects/{args.project_id}/branches/{args.branch}"
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
        cur.execute(f'GRANT USAGE ON SCHEMA {SCHEMA} TO "{client_id}"')
        cur.execute(f'GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO "{client_id}"')
        cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {SCHEMA} GRANT SELECT ON TABLES TO "{client_id}"')

    print(f"Granted SELECT on {SCHEMA}.* to app SP {client_id} ({args.app_name})")


if __name__ == "__main__":
    main()

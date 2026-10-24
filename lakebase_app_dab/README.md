# lakebase_bakehouse_viewer

A standalone Databricks App (Streamlit) that reads the synced tables produced
by the sibling `../lakebase_setup_dab` bundle, over a direct Postgres
connection to Lakebase. Kept as its own bundle — see rationale below.

## Why a separate bundle

`databricks_lakebase` is a reduced showcase of the Delta → Lakebase sync
mechanics and already has a documented first-deploy ordering issue (synced
tables need their source data to exist first). Folding a consumer app into
that same bundle would add a second, compounding ordering dependency: the
app would need the synced tables to exist *and* have completed at least one
refresh before it has anything to show. Keeping it separate means each
bundle's bootstrap story stays simple and independently fixable.

## Prerequisites

1. `../lakebase_setup_dab` is already deployed and seeded — i.e. you've
   run its `seed_source_tables` job and at least one sync refresh, so
   `sync_bakehouse.sales_franchises` / `sales_customers` / `sales_transactions`
   have rows in Postgres. See that project's README.
2. Databricks CLI >= v0.294.0, authenticated (`databricks auth profiles`).
   `<PROFILE>` in the commands below is a placeholder for whatever you named
   your profile for this workspace. Prefer an OAuth profile
   (`databricks auth login`) — `databricks apps logs` doesn't work with a PAT.
3. `uv` not required here — this app has no local dev dependencies beyond
   what's declared in `src/app/requirements.txt` (installed by the Apps
   runtime on deploy).

## This bundle's own bootstrap step

The app's service principal is created with `CAN_CONNECT_AND_CREATE` on the
Lakebase branch, which lets it create *new* schemas — but `sync_bakehouse` is
owned by the sync pipeline, not by this app. **The first deploy will raise
`permission denied for schema sync_bakehouse`** until you grant the app's SP
read access.

Each app gets its own auto-created service principal — there's no way to
assign a custom one as the app's runtime identity, and its client id isn't
known until the app resource exists. So this is necessarily a two-step,
deploy-then-grant flow; `scripts/grant_app_access.py` automates the lookup
and the grant (run as the Lakebase project owner, e.g. your own profile):

```bash
# 1. Deploy once (the app resource + SP get created even though the query will fail)
databricks bundle deploy --profile <PROFILE>
databricks bundle run bakehouse_viewer --profile <PROFILE>

# 2. Grant the app's SP read access (run from ../lakebase_setup_dab — reuses
#    its venv for databricks-sdk/psycopg rather than duplicating deps here)
cd ../lakebase_setup_dab
uv run python ../lakebase_app_dab/scripts/grant_app_access.py \
  --profile <PROFILE> --project-id lakebase-bakehouse-demo \
  --app-name bakehouse-lakebase-viewer
```

After that, reload the app — it should list row counts and a preview for
each of the 3 synced tables. Re-run the grant script if the app is ever
deleted and recreated (it gets a new SP).

## Deployment

```bash
databricks bundle validate --profile <PROFILE>
databricks bundle deploy --profile <PROFILE>
databricks bundle run bakehouse_viewer --profile <PROFILE>   # starts the app
databricks apps get bakehouse-lakebase-viewer --profile <PROFILE>  # -> app URL
```

> **Note on `resources/apps.yml`:** this was hand-written against the
> documented `postgres` app-resource shape, not generated from a live
> deploy. If `bundle validate` rejects the `postgres` block's field names,
> deploy the app once via plain CLI (`databricks apps create`, attach the
> Lakebase resource via the UI) and run
> `databricks bundle generate app --existing-app-name bakehouse-lakebase-viewer --key bakehouse_viewer`
> to get the exact schema your CLI version expects, then diff it against
> this file.

## Variables

| Variable | Default | Description |
|---|---|---|
| `lakebase_project_id` | `lakebase-bakehouse-demo` | Project id from `databricks_lakebase` |
| `lakebase_branch` | `production` | Branch to connect to |
| `lakebase_database` | `databricks-postgres` | Database *resource id* (hyphenated) — not the Postgres db name itself (`databricks_postgres`, underscored) |

## Layout

```
databricks.yml              # bundle root — variables, targets
resources/apps.yml          # app resource + postgres attachment
src/app/
  app.py                    # Streamlit UI — table picker + row preview
  app.yaml                  # Apps runtime command + env
  requirements.txt          # psycopg2-binary, pandas (not pre-installed)
```

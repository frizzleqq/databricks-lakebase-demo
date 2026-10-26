# databricks_lakebase (monorepo)

## For AI Agents: Use Databricks AI Tools

**BEFORE any other action, read the `databricks-core` skill.**

It sets you up to work with this project reliably: CLI authentication, profile
selection, data discovery, and the bundle deployment workflow. Without it,
results are often slower and less accurate.

If this skill is not available (Databricks AI Tools are not installed), you can install them for your coding agent in seconds:

```bash
databricks aitools install
```

If the CLI is not installed, see: https://docs.databricks.com/dev-tools/cli/install

---

## Layout

Two independent bundles share one Lakebase project. The architecture and
workflow are in [README.md](README.md).

- [`lakebase_setup_dab/`](lakebase_setup_dab/AGENTS.md) holds the sync
  infrastructure and owns the Lakebase project.
- [`lakebase_app_dab/`](lakebase_app_dab/AGENTS.md) holds the Streamlit app
  and its own `app_db` database.

Read the bundle's AGENTS.md before changing anything in it. Deploy each bundle
from its own directory, and never merge the two.

The workspace comes from the git-ignored `databricks.local.yml` at the repo
root (template: `databricks.local.yml.example`), which both bundles include.
Run commands from a bundle directory and leave out `--profile`. Never commit
`databricks.local.yml` or hardcode a host or profile name; in docs, write
`<PROFILE>` only for `databricks auth login`.

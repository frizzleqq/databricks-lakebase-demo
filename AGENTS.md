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

Two independent bundles share one Lakebase project. The architecture,
workflow and gotchas are in [README.md](README.md).

- [`lakebase_setup_dab/`](lakebase_setup_dab/AGENTS.md) holds the sync
  infrastructure and owns the Lakebase project.
- [`lakebase_app_dab/`](lakebase_app_dab/AGENTS.md) holds the Streamlit app
  and its own `app_db` database.

Read the bundle's AGENTS.md before changing anything in it. Deploy each bundle
from its own directory, and never merge the two.

Don't hardcode a CLI profile name in docs or commands. Use `<PROFILE>`.

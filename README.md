# databricks_lakebase

Monorepo with two independent Databricks Asset Bundles (DABs), each deployed
separately from its own directory:

| Bundle | Purpose |
|---|---|
| [`lakebase_setup_dab/`](lakebase_setup_dab/README.md) | Delta → Lakebase sync showcase (and the reverse, Lakebase → Delta CDC), using `samples.bakehouse` as sample data. |
| [`lakebase_app_dab/`](lakebase_app_dab/README.md) | Streamlit Databricks App that reads the synced tables produced by `lakebase_setup_dab`. Depends on it being deployed and seeded first. |

They're kept as separate bundles deliberately: `lakebase_setup_dab` already
has a first-deploy ordering issue of its own (synced tables need source data
to exist first — see its README's "Bootstrap ordering note"), and the app
has a smaller one too (its service principal needs a one-time grant after
first deploy). Folding both into one `bundle deploy` would compound the two.

See each bundle's own README.md for deployment steps, and AGENTS.md for
AI-agent-specific guidance.

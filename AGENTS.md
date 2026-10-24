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

This repo holds **two independent DAB bundles** as sibling directories, each
with its own `databricks.yml`, `README.md`, and `AGENTS.md`:

- [`lakebase_setup_dab/`](lakebase_setup_dab/AGENTS.md) — the Delta → Lakebase
  sync infrastructure (and reverse-sync demo). Read its AGENTS.md before
  touching Lakebase resources or jobs there.
- [`lakebase_app_dab/`](lakebase_app_dab/AGENTS.md) — a Streamlit Databricks
  App that reads `lakebase_setup_dab`'s synced tables. Depends on that bundle
  being deployed and seeded first. Read its AGENTS.md before touching it.

**Deploy each bundle from its own directory** — `cd lakebase_setup_dab` or
`cd lakebase_app_dab` first. Never try to merge them into a single
`bundle deploy`; each has its own bootstrap-ordering quirk (documented in
its own AGENTS.md/README.md) and combining them compounds both.

# Lantern Intelligence V3 — Agentic Financial Analyst

**The model chooses; SQL computes.**

V3 adds an agent layer on top of Lantern Intelligence V2. A model decides which financial metrics a question needs, requests them as tools, and answers using only the figures those tools return. Every number comes from a validated SQL query. The model never computes or invents one.

---

## From workflow to agent

Each Lantern version uses a different pattern for building LLM systems, chosen for the problem it had to solve:

| Version | Pattern | How it works |
|---|---|---|
| V1 | Routing workflow | Encoder classifiers route each input to a specialized model |
| V2 | Chaining workflow | Fixed pipeline: retrieve concepts → run SQL → local LLM interprets |
| V3 | Agent | The model chooses which tools to call, in what order, and when to stop |

V2 remains the right design for predictable, auditable answers. But it runs all 8 metric queries on every question, relevant or not, and handles one company at a time. V3 targets what a fixed pipeline can't do well: open-ended and multi-company questions where the data needed depends on the question.

In practice, a question comparing two companies' financial health leads the agent to pick 4 of the 8 metrics for each company, request all 8 calls in parallel because none depend on each other, and answer in two model calls.

---

## Design decisions

- **Built directly on the tool-use API**, without LangChain or similar frameworks, to keep control flow explicit and debuggable.
- **The model selects, SQL computes.** The agent decides which metrics a question needs, but every figure comes from one of V2's validated queries. Risk classifications, such as "Concerning" or "Safe" client concentration, are also computed in SQL rather than judged by the model.
- **Constrained tool inputs.** Company and metric arguments are restricted with JSON Schema enums, so the model can only request data that exists.
- **Read-only by construction.** Databases are opened with SQLite's `mode=ro`, so writes fail at the database level regardless of what the model requests.
- **V2 is reused, not modified.** V3 reads V2's SQL files and databases directly without importing V2's code, so V2 keeps running as its own service.
- **Failures are returned, not raised.** Tool errors go back to the model as `is_error` results, so the agent can recover or report the problem instead of crashing.
- **Bounded execution.** A step limit caps model calls per question to prevent runaway cost.
- **Swappable model layer.** All model calls go through one function, so a local model can replace the API for deployments with real client data. The prototype uses an API model for reliable tool calling on synthetic data.

---

## Architecture

```
User question
     │
     ▼
┌─────────────────────────────┐
│  Agent loop                 │◄────────────┐
│  model: Claude (API)        │             │
└─────────────┬───────────────┘             │
              │ tool requests               │ tool results
              ▼                             │
┌─────────────────────────────┐             │
│  Tools                      │─────────────┘
│  list_companies()           │
│  get_metric(company, metric)│──► V2 SQL queries ──► company SQLite DB (read-only)
└─────────────────────────────┘
```

**Metrics available:** net profit margin, monthly revenue trend, days sales outstanding, client concentration, burn rate and runway, expense breakdown, revenue per employee, client churn rate.

---

## Evaluation

Lantern uses three synthetic companies with deliberately different financial profiles, so each answer has a known expected shape. A response that describes one company with another's profile signals a context or retrieval error.

| Test | Expected behavior | Result |
|---|---|---|
| Two-company comparison | Selects relevant metrics for both companies; figures match the database | Pass |
| Single-company health check | Selects a relevant subset of metrics; inferences are hedged | Pass |
| Question outside the data | No tool calls; states the data isn't available; offers the closest available metric | Pass |
| Nonexistent company | Verifies with `list_companies`; asks for clarification | Pass |

Reported figures were spot-checked against direct SQL output: margins, concentration percentages, cash-burn months and runway matched exactly.

---

## Known limitations

- **Averaged expense data.** The synthetic data records the same expense figure every month, so month-by-month burn conclusions are less reliable than the agent's wording suggests. Spot-checking surfaced this as a data-layer issue rather than a model error.
- **Large tool results.** Some tools return full monthly or per-client rows, so input tokens grow quickly across steps. Tools that return summaries would reduce cost and latency.
- **Synthetic data only.** Not yet tested against real financial records.

---

## Roadmap

- Expose the tools through an **MCP server** so any MCP-compatible client can use them
- A repeatable **evaluation set** with expected answers, rerun after every prompt or tool change
- A guarded **fallback SQL tool** (read-only, `SELECT`-only, row limits) for questions the fixed metrics can't answer
- **Local model support** through the swappable model layer
- **Write actions with human confirmation** before any change reaches the database

---

## Running

Requires Lantern V2's `matrix_queries/` and `databases/` directories, and an `ANTHROPIC_API_KEY` in a `.env` file (excluded from version control).

```bash
pip install anthropic python-dotenv
python lantern_agent.py
```

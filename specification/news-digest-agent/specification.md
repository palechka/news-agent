# Specification: news-digest-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` at the solution root for full context.
- [x] Bootstrap agent code in `assets/news-digest-agent/` using instructions from the `sap-agent-bootstrap` section. Invoke from inside `assets/news-digest-agent/`, using copy commands — do NOT create files manually.
- [x] Install dependencies; validate the agent starts and responds at `/.well-known/agent.json`.

---

## News Fetching Tool

- [x] Create `assets/news-digest-agent/app/news_tool.py` implementing a `fetch_top_news(topic: str) -> list[dict]` function that:
  - Calls a public news API (e.g. NewsAPI.org or GNews) using the provided `topic` parameter.
  - Reads the API key from the environment variable `NEWS_API_KEY` (never hard-coded).
  - Returns a list of article dicts with at minimum: `title`, `url`, `publishedAt`, `description`, `source`.
  - Handles API errors gracefully; returns an empty list on failure and logs the error.
- [x] Register `fetch_top_news` as a LangChain `StructuredTool` (or `@tool`) in the agent's tool list.
- [x] Add `requests` (or `httpx`) to `requirements.txt` — note: the news API is an **external public API**, NOT an SAP API, so a direct HTTP call is permitted here. SAP API constraint does NOT apply to third-party public APIs.

---

## Article Selection Logic

- [x] In `assets/news-digest-agent/app/agent.py` (or a helper module), implement article ranking:
  - Accept the list returned by `fetch_top_news`.
  - Sort by `publishedAt` descending (most recent first).
  - Return the top 3 articles.
  - If fewer than 3 articles are available, proceed with however many were returned.

---

## System Prompt

- [x] In `assets/news-digest-agent/app/agent.py`, write the system prompt instructing the agent to:
  - Accept a topic from the user (politics, AI, finance, sports, technology, or any custom topic).
  - Call the `fetch_top_news` tool to retrieve articles for the given topic.
  - Select the 3 most recent and relevant articles.
  - Summarize each article in 2–4 sentences capturing the key facts.
  - Return a structured digest with: headline, source name, publication date, and summary for each article.
  - If the news API returns no results, inform the user and suggest refining the topic.
  - If summarization of an article fails, fall back to returning the headline and URL only.
  - Never fabricate, guess, or invent news content — always use the `fetch_top_news` tool.
  - Multi-topic requests are supported; call the tool once per topic.

---

## Digest Response Format

- [x] Ensure the agent's final response follows this structure for each article:

  ```
  ### [Article Number]. [Headline]
  **Source:** [Source Name] | **Published:** [Date]
  [2-4 sentence summary]
  [URL]
  ```

- [x] The digest should be readable in a conversational interface; no raw JSON output to the user.

---

## Business Instrumentation

- [x] Implement structured logging and OpenTelemetry spans for all 5 PRD milestones. Extract all business logic from `stream()` into a plain async helper (e.g. `_run_agent(query, context_id)`) to avoid `GeneratorExit` span context errors. Use the decorator or context manager form on the helper only.

  | Milestone | ID  | Log on achievement | Log on miss |
  |-----------|-----|--------------------|-------------|
  | Topic Input | M1 | `M1.achieved: topic received and news fetch initiated for topic=[topic]` | `M1.missed: no valid topic provided by user` |
  | News Fetching | M2 | `M2.achieved: news fetch completed, [n] articles retrieved for topic=[topic]` | `M2.missed: news API returned no results for topic=[topic]` |
  | Ranking & Selection | M3 | `M3.achieved: top 3 articles selected for topic=[topic]` | `M3.missed: fewer than 3 articles available; proceeding with [n] articles` |
  | Summarization | M4 | `M4.achieved: summaries generated for [n] articles` | `M4.missed: summarization failed for one or more articles` |
  | Digest Delivery | M5 | `M5.achieved: news digest delivered to user for topic=[topic]` | `M5.missed: digest delivery failed` |

- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`.

---

## MCP Tool Integration

> This agent integrates with one **external public news API** (not an SAP API) via a direct HTTP call inside `news_tool.py`. No SAP MCP servers are required for this solution. Skip all Path A / Path B / Path C MCP tasks.

- [x] Confirm `asset.yaml` does NOT list any MCP server under `requires` (no SAP MCP servers needed).
- [x] Confirm `mcp-mock.json` is generated with empty or stub tool list (no real MCP tools). Use the `mcp-mock-config` skill if needed; otherwise create a minimal `mcp-mock.json` with `{}` or an empty tools array so `conftest.py` can load it without error.

---

## Testing

- [x] Write `assets/news-digest-agent/tests/test_news_tool.py`:
  - Unit test for `fetch_top_news` — mock the HTTP call, verify article parsing and error handling.
  - Test the case where the API returns 0 articles (should return empty list, not raise).
  - Test the case where the API returns > 3 articles (verify top-3 selection).
  - Run immediately after writing.
- [x] Write `assets/news-digest-agent/tests/test_agent_integration.py`:
  - Integration test: call the agent's `invoke` function (or `stream`) with a mocked LLM and mocked `fetch_top_news` tool.
  - Assert the response contains a structured digest with at least one article headline and summary.
  - Mock AI Core / LiteLLM — no real LLM calls during tests.
  - Tests must run fully offline.
- [x] Run `pytest` from `assets/news-digest-agent/` (no args) — fix any failures before proceeding.
- [x] Confirm coverage ≥ 70%; add targeted tests if below threshold. (78% achieved)
- [x] Run `pytest` again (no args) to produce final `test_report.json`.
- [x] Verify `assets/news-digest-agent/test_report.json` exists.

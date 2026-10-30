# Product Requirements Document (PRD)

**Title:** News Digest Agent  
**Date:** 2026-10-30  
**Solution Category:** AI Agent

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Business users waste up to 30 minutes daily scanning multiple news sources across topics like politics, AI, and finance. This agent delivers an on-demand, LLM-powered digest of the top 3 news stories for any topic — instantly.

**Business Need:**  
Professionals need to stay informed on fast-moving topics without the overhead of manually aggregating and reading multiple sources. There is no standard SAP product that covers external news aggregation and summarization.

**Expected Value:**  
Save 30 minutes per user per day currently spent on manual news monitoring.

**Product Objectives:**
1. Deliver a concise, accurate top-3 news digest for any requested topic within seconds.
2. Summarize articles in plain language, highlighting the key point of each story.
3. Support a broad range of topics (politics, AI, finance, sports, technology, etc.).

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time saved per user per day on manual news monitoring | — | 30 min/day | — | Daily news intelligence consumption | user |

## Requirements

### Must-Have Requirements

**R1**: Topic-Based News Fetching
- **Problem to Solve**: Users have no automated way to retrieve current news for a specific topic.
- **User Story**: As a business user, I need to specify a topic and receive today's top news articles so that I stay informed without manual searching.
- **Acceptance Criteria**:
  - Given a topic keyword (e.g., "AI"), when I ask the agent, then it retrieves at least 3 relevant news articles published today or within the last 24 hours.
- **Priority Rank**: 1

**R2**: Top-3 Article Selection
- **Problem to Solve**: Raw news feeds contain too many articles; users need the most relevant ones surfaced.
- **User Story**: As a business user, I need the agent to identify the 3 most relevant and recent articles so that I don't have to sift through noise.
- **Acceptance Criteria**:
  - Given multiple retrieved articles, when the agent processes them, then exactly 3 are selected based on recency and relevance.
- **Priority Rank**: 2

**R3**: LLM-Powered Summarization
- **Problem to Solve**: Full articles take time to read; users need concise summaries.
- **User Story**: As a business user, I need a short summary of each article so that I can grasp the key point in under 30 seconds.
- **Acceptance Criteria**:
  - Given 3 selected articles, when summarized, then each summary is 2–4 sentences and captures the key facts.
- **Priority Rank**: 3

**R4**: Structured Digest Response
- **Problem to Solve**: Unformatted output is hard to scan quickly.
- **User Story**: As a business user, I need the digest returned in a clear, readable format so that I can quickly scan all 3 stories.
- **Acceptance Criteria**:
  - Given 3 summaries, when returned, the response includes a title, source, date, and summary for each article.
- **Priority Rank**: 4

**R5**: Multi-Topic Support
- **Problem to Solve**: Users follow diverse topics and need flexibility.
- **User Story**: As a business user, I need to request news on any topic (politics, finance, AI, sports, etc.) so that the agent is useful across my different interests.
- **Acceptance Criteria**:
  - Given any topic string, the agent handles it without hard-coded topic restrictions.
- **Priority Rank**: 5

## Solution Architecture

**Architecture Overview:**  
A Python-based A2A agent hosted on SAP AI Core. The agent accepts a topic from the user, calls an external news API tool to fetch articles, selects the top 3, and invokes the SAP Generative AI Hub LLM to produce summaries. The final digest is returned as a conversational response.

**Key Components:**
- **News Digest Agent** (Python, A2A protocol): Core reasoning and orchestration
- **News API Tool**: Fetches recent articles from a public news API (e.g., NewsAPI.org, GNews)
- **SAP Generative AI Hub (LLM)**: Summarizes article content

**Integration Points:**
- External News API: outbound read-only call, on-demand per user request

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent is designed with modular tools; additional news sources or topic-specific feeds can be added as new tools without changing core agent logic.
- Summarization style (brief / detailed / bullet points) is configurable via system prompt parameters.

**Business Step Instrumentation:**
- Each milestone emits a structured log for observability in production.
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent

**Actions the system performs without human approval:**
- Query external news API for a given topic
- Select top 3 articles by recency and relevance
- Generate LLM summaries for each article
- Return formatted digest to user

**Actions that require human review or approval:**
- None — all actions are read-only and informational

**Model or engine used:** SAP Generative AI Hub (GPT-4o or equivalent)

**Knowledge & data sources accessed:**
- External public news API (read-only, no PII involved)

**Tools or connectors invoked:**
- `fetch_top_news(topic)`: Calls external news API, returns list of articles — read-only
- SAP Generative AI Hub LLM: Summarizes article text — read-only

**Guardrails & fail-safes:**
- If the news API returns no results, the agent informs the user and suggests refining the topic.
- If the LLM summarization fails, the agent falls back to returning the article headline and URL.
- The agent never stores, forwards, or persists article content beyond the current conversation turn.

## Milestones

### M1: Topic Input

- **Description**: User provides a topic; the agent acknowledges and begins processing.
- **Achieved when**: A valid topic string is received and passed to the news fetch tool.
- **Log on achievement**: `M1.achieved: topic received and news fetch initiated for topic=[topic]`
- **Log on miss**: `M1.missed: no valid topic provided by user`

### M2: News Fetching

- **Description**: Agent retrieves candidate articles from the external news API.
- **Achieved when**: At least 1 article is returned by the news API for the given topic.
- **Log on achievement**: `M2.achieved: news fetch completed, [n] articles retrieved for topic=[topic]`
- **Log on miss**: `M2.missed: news API returned no results for topic=[topic]`

### M3: Ranking & Selection

- **Description**: Agent selects the top 3 most relevant and recent articles.
- **Achieved when**: Exactly 3 articles are selected for summarization.
- **Log on achievement**: `M3.achieved: top 3 articles selected for topic=[topic]`
- **Log on miss**: `M3.missed: fewer than 3 articles available; proceeding with [n] articles`

### M4: Summarization

- **Description**: LLM generates a concise summary for each selected article.
- **Achieved when**: All selected articles have a non-empty summary generated.
- **Log on achievement**: `M4.achieved: summaries generated for [n] articles`
- **Log on miss**: `M4.missed: summarization failed for one or more articles`

### M5: Digest Delivery

- **Description**: The agent returns the structured news digest to the user.
- **Achieved when**: The formatted response containing titles, sources, dates, and summaries is delivered.
- **Log on achievement**: `M5.achieved: news digest delivered to user for topic=[topic]`
- **Log on miss**: `M5.missed: digest delivery failed`

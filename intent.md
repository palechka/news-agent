# News Digest Agent

AI agent that fetches and summarizes the top 3 news of the day on user-specified topics such as politics, AI, and finance.

## Business challenge

Business users spend significant time each day manually scanning multiple news sources to stay informed on topics relevant to their work. An AI agent should automate this by fetching, ranking, and summarizing the top 3 news stories of the day for any requested topic, delivering a concise digest on demand.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time saved per user per day on manual news monitoring | — | 30 min/day | — | Daily news intelligence consumption | user |

## Key Milestones

1. **Topic Input** — User specifies one or more topics (e.g. politics, AI, finance); agent acknowledges and begins retrieval.
2. **News Fetching** — Agent queries external news sources and retrieves candidate articles for the requested topic.
3. **Ranking & Selection** — Agent selects the top 3 most relevant and recent articles.
4. **Summarization** — Agent generates a concise summary for each of the 3 articles.
5. **Digest Delivery** — Agent returns a structured, readable news digest to the user.

## Business Architecture (RBA)

### End-to-End Process

Manage Information Technology

### Process Hierarchy

```
Manage Information Technology
└── Manage Information Technology (Phase)
    └── Manage enterprise information
        └── Manage business information
```

### Summary

The news digest agent maps to "Manage enterprise information" — collecting, processing, and delivering the right information to the right people at the right time to support business decision-making.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
|---|---|---|---|---|---|---|---|---|
| Fetch top news articles by topic from external sources | None | — | — | — | — | — | Yes | Requires integration with a public news API (e.g. NewsAPI, GNews, or similar) |
| Summarize and rank articles using LLM | None | — | — | — | — | — | Yes | Custom LLM-based summarization via SAP AI Core / generative AI hub |
| Deliver structured digest to user on demand | None | — | — | — | — | — | Yes | Delivered via agent response in conversational interface |

### Key findings

- No standard SAP product covers external news aggregation or summarization out of the box.
- The solution requires a custom Python AI agent that integrates with a public news API and uses an LLM for summarization.
- SAP AI Core / generative AI hub provides the LLM runtime for summarization.
- The agent will be built using the A2A (Agent-to-Agent) protocol as a pro-code Python agent.
- External news API access (e.g. NewsAPI.org) is assumed to be available; an API key will be required at runtime.

## Recommendations

### AI News Digest Agent

#### Executive Summary

Custom Python AI agent fetching & summarizing top 3 daily news per topic.

#### Recommended Solution

A pro-code Python agent (A2A protocol) that accepts a topic from the user, calls an external news API to retrieve recent articles, selects the top 3, and uses an LLM via SAP AI Core to generate concise summaries. The digest is returned as a structured conversational response.

#### Recommended solution category

AI Agent

#### Intent fit
95%

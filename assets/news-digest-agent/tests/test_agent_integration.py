"""Integration test for the News Digest Agent end-to-end flow."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from agent import SampleAgent, get_system_prompt


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def mock_news_articles():
    return [
        {
            "title": "AI Model Sets New Benchmark",
            "url": "https://example.com/ai-benchmark",
            "publishedAt": "2024-10-30T11:00:00Z",
            "description": "A new AI model has set a world record on a leading benchmark.",
            "source": "Tech Today",
        },
        {
            "title": "OpenAI Announces Partnership",
            "url": "https://example.com/openai-partnership",
            "publishedAt": "2024-10-30T09:00:00Z",
            "description": "OpenAI has announced a major partnership with a Fortune 500 company.",
            "source": "Business Wire",
        },
        {
            "title": "EU Passes AI Regulation",
            "url": "https://example.com/eu-ai-regulation",
            "publishedAt": "2024-10-29T15:00:00Z",
            "description": "The European Union has officially passed its AI regulation framework.",
            "source": "Reuters",
        },
    ]


@pytest.fixture
def digest_response_text(mock_news_articles):
    """Canned LLM response simulating a formatted news digest."""
    return (
        "### 1. AI Model Sets New Benchmark\n"
        "**Source:** Tech Today | **Published:** 2024-10-30\n"
        "A new AI model has set a world record. This is a major milestone for AI research.\n"
        "https://example.com/ai-benchmark\n\n"
        "### 2. OpenAI Announces Partnership\n"
        "**Source:** Business Wire | **Published:** 2024-10-30\n"
        "OpenAI announced a major business partnership.\n"
        "https://example.com/openai-partnership\n\n"
        "### 3. EU Passes AI Regulation\n"
        "**Source:** Reuters | **Published:** 2024-10-29\n"
        "The EU has formally adopted its AI regulatory framework.\n"
        "https://example.com/eu-ai-regulation"
    )


# --------------------------------------------------------------------------- #
# Integration test
# --------------------------------------------------------------------------- #

class TestNewsDigestAgentIntegration:

    @pytest.mark.asyncio
    async def test_full_flow_returns_news_digest(self, mock_news_articles, digest_response_text):
        """Test that the agent calls fetch_top_news and returns a formatted digest."""

        # Mock the LLM to return a canned digest response
        mock_llm_response = AIMessage(content=digest_response_text)
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {"messages": [mock_llm_response]}

        agent = SampleAgent()

        # Patch _create_graph to return our mock graph (avoids real LLM calls)
        with patch.object(agent, "_create_graph", return_value=mock_graph):
            @tool
            def fetch_top_news(topic: str) -> list:
                """Fetch top news articles for a topic."""
                return mock_news_articles

            result = await agent.invoke(
                query="Give me the top AI news today",
                context_id="test-context-001",
                tools=[fetch_top_news],
            )

        assert result.status == "completed"
        assert result.message == digest_response_text

    @pytest.mark.asyncio
    async def test_stream_yields_processing_then_result(self, digest_response_text):
        """Test that stream() yields a 'Processing...' status before the final result."""
        mock_llm_response = AIMessage(content=digest_response_text)
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {"messages": [mock_llm_response]}

        agent = SampleAgent()

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            chunks = []
            async for chunk in agent.stream(
                query="Top finance news",
                context_id="test-context-002",
                tools=[],
            ):
                chunks.append(chunk)

        assert len(chunks) >= 2
        # First chunk is the working status
        assert chunks[0]["is_task_complete"] is False
        assert "Processing" in chunks[0]["content"]
        # Last chunk is the completed response
        assert chunks[-1]["is_task_complete"] is True
        assert chunks[-1]["content"] == digest_response_text

    @pytest.mark.asyncio
    async def test_agent_handles_no_tools_gracefully(self):
        """Test that agent handles the case where no tools are available."""
        canned_response = "Tools are temporarily unavailable."
        mock_llm_response = AIMessage(content=canned_response)
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {"messages": [mock_llm_response]}

        agent = SampleAgent()

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="Give me politics news",
                context_id="test-context-003",
                tools=[],
            )

        assert result.status == "completed"
        assert result.message == canned_response

    @pytest.mark.asyncio
    async def test_agent_handles_llm_exception_gracefully(self):
        """Test that stream() handles unexpected LLM errors gracefully."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = RuntimeError("Unexpected LLM error")

        agent = SampleAgent()

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            result = await agent.invoke(
                query="Top politics news",
                context_id="test-context-004",
                tools=[],
            )

        # The agent catches exceptions and returns a completed status with an error message
        assert result.status in ("completed", "error")
        assert "error" in result.message.lower()

    def test_system_prompt_contains_key_instructions(self):
        """Test that the system prompt includes all key behavioral instructions."""
        prompt = get_system_prompt()
        assert "fetch_top_news" in prompt
        assert "topic" in prompt.lower()
        assert "fabricate" in prompt.lower() or "invent" in prompt.lower()
        assert "3" in prompt  # top 3 articles

    @pytest.mark.asyncio
    async def test_milestones_logged(self, mock_news_articles, digest_response_text, caplog):
        """Test that milestone log messages are emitted during agent execution."""
        import logging
        mock_llm_response = AIMessage(content=digest_response_text)
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {"messages": [mock_llm_response]}

        agent = SampleAgent()

        with patch.object(agent, "_create_graph", return_value=mock_graph):
            with caplog.at_level(logging.INFO, logger="agent"):
                result = await agent.invoke(
                    query="AI news",
                    context_id="test-context-milestone",
                    tools=[],
                )

        log_messages = " ".join(caplog.messages)
        # At least M1 and M5 should be logged
        assert "M1.achieved" in log_messages
        assert "M5.achieved" in log_messages
        assert result.status == "completed"

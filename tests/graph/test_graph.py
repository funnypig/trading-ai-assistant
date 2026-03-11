from unittest.mock import patch

import pytest

from src.app.domain.schemas import AgentOutput, TaskClassificationResult
from src.app.graph.graph import build_graph

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

MOCK_FUNDAMENTAL = AgentOutput(source="Fundamental Analysis", result="mock fundamental")
MOCK_SENTIMENT = AgentOutput(source="Sentiment Analysis", result="mock sentiment")
MOCK_OPTION = AgentOutput(source="Option Analysis", result="mock option")
MOCK_FINAL = "mock synthesized answer"


def _make_classification(**kwargs) -> TaskClassificationResult:
    defaults = dict(
        task_type="immediate",
        task_schedule=None,
        task_query=None,
        agent_query="analyze AAPL",
        agent_queries={},
        invoke_agents=[],
        ticker="AAPL",
    )
    defaults.update(kwargs)
    return TaskClassificationResult(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def graph():
    """Build the graph with all LLM-dependent nodes mocked out."""
    with (
        patch("src.app.agents.nodes.task_classification_node.TaskClassificationNode.__call__") as mock_classify,
        patch("src.app.agents.nodes.fundamental_analysis_node.FundamentalAnalysisNode.__call__") as mock_fund,
        patch("src.app.agents.nodes.sentiment_analysis_node.SentimentAnalysisNode.__call__") as mock_sent,
        patch("src.app.agents.nodes.option_analysis_node.OptionAnalysisNode.__call__") as mock_opt,
        patch("src.app.agents.nodes.synthesize_node.SynthesizeNode.__call__") as mock_synth,
        patch("src.app.agents.nodes.recurring_task_node.RecurringTaskNode.__call__") as mock_recurring,
        patch("langchain.chat_models.init_chat_model"),
    ):
        compiled = build_graph()
        yield compiled, mock_classify, mock_fund, mock_sent, mock_opt, mock_synth, mock_recurring


# ---------------------------------------------------------------------------
# Test 2 — single-agent immediate task
# ---------------------------------------------------------------------------

def test_immediate_single_agent(graph):
    compiled, mock_classify, mock_fund, mock_sent, mock_opt, mock_synth, mock_recurring = graph

    classification = _make_classification(
        invoke_agents=["fundamental"],
        agent_queries={"fundamental": "What does fundamental analysis say about AAPL?"},
    )
    mock_classify.return_value = {"task_classification": classification}
    mock_fund.return_value = {"results": [MOCK_FUNDAMENTAL]}
    mock_synth.return_value = {"final_answer": MOCK_FINAL}

    result = compiled.invoke({"query": "Analyze AAPL fundamentals"})

    mock_fund.assert_called_once()
    mock_sent.assert_not_called()
    mock_opt.assert_not_called()
    mock_recurring.assert_not_called()

    assert result["results"] == [MOCK_FUNDAMENTAL]
    assert result["final_answer"] == MOCK_FINAL


# ---------------------------------------------------------------------------
# Test 3 — multi-agent immediate task (fan-out + fan-in)
# ---------------------------------------------------------------------------

def test_immediate_multi_agent(graph):
    compiled, mock_classify, mock_fund, mock_sent, mock_opt, mock_synth, mock_recurring = graph

    classification = _make_classification(
        invoke_agents=["fundamental", "sentiment", "option"],
        agent_queries={
            "fundamental": "What does fundamental analysis say about AAPL?",
            "sentiment": "What does market sentiment say about AAPL?",
            "option": "What does the options market indicate about AAPL?",
        },
    )
    mock_classify.return_value = {"task_classification": classification}
    mock_fund.return_value = {"results": [MOCK_FUNDAMENTAL]}
    mock_sent.return_value = {"results": [MOCK_SENTIMENT]}
    mock_opt.return_value = {"results": [MOCK_OPTION]}
    mock_synth.return_value = {"final_answer": MOCK_FINAL}

    result = compiled.invoke({"query": "Full analysis of AAPL"})

    mock_fund.assert_called_once()
    mock_sent.assert_called_once()
    mock_opt.assert_called_once()
    mock_recurring.assert_not_called()

    assert len(result["results"]) == 3
    sources = {r["source"] for r in result["results"]}
    assert sources == {"Fundamental Analysis", "Sentiment Analysis", "Option Analysis"}
    assert result["final_answer"] == MOCK_FINAL


# ---------------------------------------------------------------------------
# Test 4 — recurring task (mock path, analysis nodes not called)
# ---------------------------------------------------------------------------

def test_recurring_task(graph):
    compiled, mock_classify, mock_fund, mock_sent, mock_opt, mock_synth, mock_recurring = graph

    classification = _make_classification(
        task_type="recurring",
        task_schedule="4H",
        task_query="Alert when AAPL drops below 200 EMA",
        invoke_agents=[],
    )
    mock_classify.return_value = {"task_classification": classification}
    mock_recurring.return_value = {
        "final_answer": "Recurring task scheduled.\nSchedule: 4H\nTask: Alert when AAPL drops below 200 EMA"
    }

    result = compiled.invoke({"query": "Alert me every 4h if AAPL drops below 200 EMA"})

    mock_recurring.assert_called_once()
    mock_fund.assert_not_called()
    mock_sent.assert_not_called()
    mock_opt.assert_not_called()
    mock_synth.assert_not_called()

    assert "4H" in result["final_answer"]
    assert "200 EMA" in result["final_answer"]

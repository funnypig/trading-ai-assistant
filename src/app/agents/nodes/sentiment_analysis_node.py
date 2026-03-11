from src.app.domain.schemas import AgentState, AgentOutput
from src.app.agents.sentiment_agent import sentiment_analysis_agent
from src.app.tools.news.registry import init as init_registry


class SentimentAnalysisNode:
    def __init__(self):
        self.agent = sentiment_analysis_agent
        self.name = "Sentiment Analysis"

    def __call__(self, state: AgentState):
        init_registry()
        query = state.task_classification.agent_queries.get("sentiment") or state.task_classification.agent_query
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        answer = result["messages"][-1].content
        output = AgentOutput(
            source=self.name,
            result=answer,
        )

        return dict(results=[output])

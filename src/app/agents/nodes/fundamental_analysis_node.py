from src.app.domain.schemas import AgentState, AgentOutput
from src.app.agents.fundamental_agent import fundamental_analysis_agent


class FundamentalAnalysisNode:
    def __init__(self):
        self.agent = fundamental_analysis_agent
        self.name = "Fundamental Analysis"

    def __call__(self, state: AgentState):
        query = state.task_classification.agent_queries.get("fundamental") or state.task_classification.agent_query
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        answer = result["messages"][-1].content
        output = AgentOutput(
            source=self.name,
            result=answer,
        )

        return dict(results=[output])

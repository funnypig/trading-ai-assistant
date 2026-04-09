from src.app.graph.state import AgentState, AgentOutput
from src.app.agents.fundamental_agent import fundamental_analysis_agent


class FundamentalAnalysisNode:
    def __init__(self):
        self.agent = fundamental_analysis_agent
        self.name = "Fundamental Analysis"

    def __call__(self, state: AgentState):
        tc = state["task_classification"]
        query = tc.agent_queries.get("fundamental") or tc.agent_query
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        answer = result["messages"][-1].content
        output = AgentOutput(
            source=self.name,
            result=answer,
        )

        return dict(results=[output])

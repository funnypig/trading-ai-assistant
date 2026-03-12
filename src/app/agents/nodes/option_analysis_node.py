from src.app.domain.schemas import AgentState, AgentOutput
from src.app.agents.option_agent import options_analysis_agent


class OptionAnalysisNode:
    def __init__(self):
        self.agent = options_analysis_agent
        self.name = "Option Analysis"

    def __call__(self, state: AgentState):
        # TODO: save observations to analyze dynamic in future
        tc = state["task_classification"]
        query = tc.agent_queries.get("option") or tc.agent_query
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        answer = result["messages"][-1].content
        output = AgentOutput(
            source=self.name,
            result=answer,
        )

        return dict(results=[output])

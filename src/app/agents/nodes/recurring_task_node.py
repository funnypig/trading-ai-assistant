from src.app.domain.schemas import AgentState


class RecurringTaskNode:
    def __call__(self, state: AgentState) -> dict:
        tc = state.task_classification
        answer = (
            f"Recurring task scheduled.\n"
            f"Schedule: {tc.task_schedule}\n"
            f"Task: {tc.task_query}\n"
            f"(Scheduling not yet implemented)"
        )
        return dict(final_answer=answer)

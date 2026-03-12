import argparse

from langchain_core.messages import HumanMessage

from src.app.graph.graph import build_graph

NODE_LABELS = {
    "task_classification": "Classifying task",
    "option": "Running option analysis",
    "fundamental": "Running fundamental analysis",
    "sentiment": "Running sentiment analysis",
    "synthesize": "Synthesizing answer",
    "recurring_task": "Scheduling recurring task",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--message", required=True, nargs="+", help="Query to send to the agent")
    args = parser.parse_args()

    query = " ".join(args.message)
    graph = build_graph()

    final_answer = None
    for chunk in graph.stream(
        {"query": query, "messages": [HumanMessage(content=query)], "results": []},
        stream_mode="updates",
    ):
        for node, update in chunk.items():
            label = NODE_LABELS.get(node, node)
            print(f"\n[{label}]")

            if node == "task_classification":
                tc = update.get("task_classification")
                if tc:
                    agents = tc.invoke_agents or ["none — answering from context"]
                    print(f"  agents : {agents}")
                    print(f"  ticker : {tc.ticker}")
                    print(f"  type   : {tc.task_type}")

            elif node in ("option", "fundamental", "sentiment"):
                for r in update.get("results", []):
                    preview = r["result"][:200].replace("\n", " ")
                    print(f"  {r['source']}: {preview}...")

            elif node == "synthesize":
                final_answer = update.get("final_answer", "")

    print("\n" + "─" * 60)
    print(final_answer or "No answer produced.")


if __name__ == "__main__":
    main()

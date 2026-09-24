import logging
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from pipeline_graph import build_pipeline_graph

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    query = input("Research question: ").strip()

    graph = build_pipeline_graph(checkpointer=MemorySaver())   # ← REQUIRED
    config = {"configurable": {"thread_id": "review-1"}}

    result = graph.invoke({"query": query}, config=config)

    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print(f"\n>> {payload['prompt']}")

        choice = input(
            "Approve all [y] / remove some [2,5] / quit [q]: "
        ).strip().lower()

        if choice == "q":
            print("Aborted.")
            return

        if choice in ("", "y"):
            decision = {"action": "approve_all"}
        else:
            try:
                decision = {"action": "remove",
                            "remove": [int(x) for x in choice.split(",")]}
            except ValueError:
                print("Unrecognized input — approving all.")
                decision = {"action": "approve_all"}

        # Resume with the human's decision — Command(resume=...) is
        # the correct API for passing values INTO interrupt()
        result = graph.invoke(Command(resume=decision), config=config)

    print("\n" + "=" * 70)
    print(f"DONE — final report saved to: {result['report_path']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
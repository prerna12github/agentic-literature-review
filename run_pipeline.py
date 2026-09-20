import json
from pipeline_graph import build_pipeline_graph


def main():
    query = input("Research question: ").strip()
    graph = build_pipeline_graph()

    config = {"configurable": {"thread_id": "review-1"}}  # needed for resume
    result = graph.invoke({"query": query}, config=config)

    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print(f"\n>> {payload['prompt']}")

        choice = input("Approve all [y] / remove some [2,5] / quit [q]: ").strip().lower()
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

        # Resume the graph with the human's decision
        result = graph.invoke(None, config=config)  
    print("\n" + "=" * 70)
    print("DONE — final report:")
    print(result["report_path"])
    print("=" * 70)


if __name__ == "__main__":
    main()
import argparse
from pathlib import Path

from src.app.graph.graph import build_graph


def main():
    parser = argparse.ArgumentParser(description="Save agent graph visualization")
    parser.add_argument("-o", "--output", default="docs/graph", help="Output filename without extension (default: docs/graph)")
    parser.add_argument("--mermaid", action="store_true", help="Save as mermaid markdown instead of PNG")
    args = parser.parse_args()

    graph = build_graph()
    g = graph.get_graph()

    if args.mermaid:
        path = Path(f"{args.output}.md")
        path.write_text(f"```mermaid\n{g.draw_mermaid()}\n```\n")
        print(f"Saved mermaid diagram to {path}")
    else:
        path = Path(f"{args.output}.png")
        path.write_bytes(g.draw_mermaid_png())
        print(f"Saved graph visualization to {path}")


if __name__ == "__main__":
    main()

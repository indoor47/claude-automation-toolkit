#!/usr/bin/env python3
"""
data_analyzer.py — Natural language Q&A over CSV/JSON data using Claude.

Usage:
    python data_analyzer.py sales.csv "what's the top performing product?"
    python data_analyzer.py data.json "summarize trends by month"
    python data_analyzer.py sales.csv --interactive   # Q&A loop
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

client = anthropic.Anthropic()


def load_data(path: Path) -> tuple[str, str]:
    """Load CSV or JSON data. Returns (content_string, format)."""
    suffix = path.suffix.lower()

    if suffix == ".csv":
        try:
            import pandas as pd
            df = pd.read_csv(path)
            # Show schema + sample
            info = f"Columns: {list(df.columns)}\nShape: {df.shape[0]} rows × {df.shape[1]} cols\n"
            info += f"Data types:\n{df.dtypes.to_string()}\n\n"
            info += f"First 10 rows:\n{df.head(10).to_string()}\n\n"
            if df.shape[0] > 10:
                info += f"Basic stats:\n{df.describe().to_string()}"
            return info, "csv"
        except ImportError:
            # Fallback: raw text
            content = path.read_text(encoding="utf-8", errors="replace")
            return content[:8000], "csv_raw"

    elif suffix == ".json":
        content = path.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(content)
            # Truncate large objects
            formatted = json.dumps(data, indent=2)[:8000]
            if len(formatted) < len(json.dumps(data, indent=2)):
                formatted += "\n... [truncated]"
            return formatted, "json"
        except json.JSONDecodeError:
            return content[:8000], "json_raw"

    else:
        return path.read_text(encoding="utf-8", errors="replace")[:8000], "text"


def ask_about_data(data_content: str, filename: str, question: str, history: list = None) -> str:
    """Ask Claude a question about the data."""
    messages = []

    # System context
    system = f"""You are a data analyst assistant. The user has loaded a file called "{filename}".

Here is the data:

{data_content}

Answer questions about this data clearly and concisely. When relevant:
- Show specific numbers and examples from the data
- Point out interesting patterns or anomalies
- Suggest follow-up questions if useful"""

    # Add conversation history if in interactive mode
    if history:
        for h in history:
            messages.append(h)

    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=messages,
    )

    return response.content[0].text


def interactive_mode(path: Path, data_content: str, fmt: str):
    """Interactive Q&A loop."""
    print(f"\nData loaded: {path.name} ({fmt})")
    print("Ask questions about your data. Type 'quit' to exit.\n")

    history = []

    while True:
        question = input("Question > ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        print("\nAnalyzing...")
        answer = ask_about_data(data_content, path.name, question, history)

        print(f"\n{answer}\n")

        # Keep history for context
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

        # Trim history if too long
        if len(history) > 20:
            history = history[-20:]


def main():
    parser = argparse.ArgumentParser(description="Natural language data analysis with Claude")
    parser.add_argument("file", help="CSV or JSON file to analyze")
    parser.add_argument("question", nargs="?", help="Question to ask about the data")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive Q&A mode")
    parser.add_argument("--output", "-o", help="Save answer to file")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)

    print(f"Loading {path.name}...")
    data_content, fmt = load_data(path)
    print(f"Loaded ({fmt}, {len(data_content)} chars)")

    if args.interactive:
        interactive_mode(path, data_content, fmt)
        return

    if not args.question:
        parser.print_help()
        sys.exit(1)

    print(f"\nAnalyzing: {args.question}\n")
    answer = ask_about_data(data_content, path.name, args.question)

    if args.output:
        Path(args.output).write_text(answer)
        print(f"Answer saved to: {args.output}")
    else:
        print(answer)


if __name__ == "__main__":
    main()

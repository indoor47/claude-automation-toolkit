#!/usr/bin/env python3
"""
chat_with_files.py — Chat with any collection of documents using Claude.

Usage:
    python chat_with_files.py ./docs/
    python chat_with_files.py contract.pdf notes.txt README.md
    python chat_with_files.py ./codebase/ --filter "*.py"
"""

import argparse
import fnmatch
import os
import sys
from pathlib import Path

import anthropic

client = anthropic.Anthropic()

SUPPORTED = {".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
             ".html", ".css", ".csv", ".xml", ".toml", ".ini", ".cfg", ".sh",
             ".go", ".rs", ".java", ".c", ".cpp", ".h", ".rb", ".php"}
MAX_CONTENT = 100_000  # ~100k chars total context limit


def collect_files(sources: list[str], filter_pattern: str = "") -> list[Path]:
    """Collect all files from paths/directories."""
    files = []
    for source in sources:
        p = Path(source)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in SUPPORTED:
                    # Skip common noise
                    if any(part in f.parts for part in
                           ("node_modules", ".git", "__pycache__", "venv", ".venv", "dist")):
                        continue
                    if filter_pattern and not fnmatch.fnmatch(f.name, filter_pattern):
                        continue
                    files.append(f)
    return files


def read_files(files: list[Path]) -> dict[str, str]:
    """Read files, respecting total size limit."""
    contents = {}
    total = 0

    for f in files:
        if total >= MAX_CONTENT:
            print(f"  [limit] Reached {MAX_CONTENT} char limit, skipping remaining files")
            break

        if f.suffix.lower() == ".pdf":
            try:
                import pypdf2
                reader = pypdf2.PdfReader(str(f))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                print(f"  [skip] {f.name} — install pypdf2 for PDF support")
                continue
            except Exception as e:
                print(f"  [error] {f.name}: {e}")
                continue
        else:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                print(f"  [error] {f.name}: {e}")
                continue

        remaining = MAX_CONTENT - total
        if len(text) > remaining:
            text = text[:remaining] + "\n[... truncated]"

        contents[str(f)] = text
        total += len(text)
        print(f"  Loaded: {f.name} ({len(text)} chars)")

    return contents


def build_context(contents: dict[str, str]) -> str:
    """Build a formatted context string from all files."""
    parts = []
    for path, content in contents.items():
        parts.append(f"=== FILE: {path} ===\n{content}\n=== END: {path} ===")
    return "\n\n".join(parts)


def chat(context: str, question: str, history: list) -> str:
    """Send a message with document context."""
    system = f"""You have access to the following documents. Answer questions based on their content.
If information isn't in the documents, say so clearly.

DOCUMENTS:
{context}"""

    messages = list(history) + [{"role": "user", "content": question}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Chat with your documents using Claude")
    parser.add_argument("sources", nargs="+", help="Files or directories to load")
    parser.add_argument("--filter", "-f", default="", help="Filter pattern (e.g. '*.py')")
    parser.add_argument("--question", "-q", help="One-shot question (non-interactive)")
    parser.add_argument("--output", "-o", help="Save response to file (with --question)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    print("Collecting files...")
    files = collect_files(args.sources, args.filter)

    if not files:
        print("No supported files found.")
        sys.exit(1)

    print(f"Found {len(files)} files. Loading...")
    contents = read_files(files)

    if not contents:
        print("No readable content found.")
        sys.exit(1)

    total_chars = sum(len(v) for v in contents.values())
    print(f"\nLoaded {len(contents)} files ({total_chars:,} chars total)\n")

    context = build_context(contents)

    # One-shot mode
    if args.question:
        print(f"Q: {args.question}\n")
        answer = chat(context, args.question, [])
        if args.output:
            Path(args.output).write_text(answer)
            print(f"Answer saved to: {args.output}")
        else:
            print(answer)
        return

    # Interactive mode
    print("Ready. Ask questions about your documents (type 'quit' to exit).\n")
    history = []

    while True:
        question = input("You > ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        print("\nThinking...\n")
        answer = chat(context, question, history)
        print(f"Claude > {answer}\n")

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

        # Keep history manageable
        if len(history) > 20:
            history = history[-20:]


if __name__ == "__main__":
    main()

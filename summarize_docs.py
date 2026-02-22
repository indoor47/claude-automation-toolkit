#!/usr/bin/env python3
"""
summarize_docs.py — Batch summarize a folder of documents using Claude.

Usage:
    python summarize_docs.py ./docs/              # summarize all files
    python summarize_docs.py ./docs/ --format md  # output as markdown
    python summarize_docs.py report.txt           # single file
"""

import argparse
import os
import sys
from pathlib import Path

import anthropic

SUPPORTED = {".txt", ".md", ".py", ".js", ".ts", ".html", ".csv", ".json", ".yaml", ".yml"}

client = anthropic.Anthropic()


def read_file(path: Path) -> str | None:
    """Read a text file. Try PDF via pypdf2 if installed."""
    if path.suffix.lower() == ".pdf":
        try:
            import pypdf2
            reader = pypdf2.PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            print(f"  [skip] {path.name} — install pypdf2 for PDF support")
            return None
        except Exception as e:
            print(f"  [error] {path.name}: {e}")
            return None

    if path.suffix.lower() not in SUPPORTED:
        return None

    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [error] {path.name}: {e}")
        return None


def summarize(content: str, filename: str, style: str = "bullet") -> str:
    """Call Claude to summarize the content."""
    if style == "bullet":
        instruction = "Summarize the key points as a concise bullet list (5-10 bullets max)."
    elif style == "paragraph":
        instruction = "Write a 2-3 paragraph executive summary."
    else:
        instruction = "Provide a one-sentence TL;DR followed by key details."

    prompt = f"""File: {filename}

{instruction}

Content:
{content[:8000]}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def process_path(target: Path, style: str, output_format: str) -> list[tuple[str, str]]:
    """Process a file or directory. Returns list of (filename, summary) pairs."""
    results = []

    if target.is_file():
        content = read_file(target)
        if content:
            print(f"Summarizing: {target.name}...")
            summary = summarize(content, target.name, style)
            results.append((target.name, summary))
    elif target.is_dir():
        files = sorted(
            p for p in target.rglob("*")
            if p.is_file() and (p.suffix.lower() in SUPPORTED or p.suffix.lower() == ".pdf")
        )
        if not files:
            print(f"No supported files found in {target}")
            return results
        print(f"Found {len(files)} files to summarize...")
        for f in files:
            content = read_file(f)
            if content:
                print(f"  Summarizing: {f.name}...")
                summary = summarize(content, f.name, style)
                results.append((str(f.relative_to(target)), summary))
    else:
        print(f"Error: {target} not found")

    return results


def format_output(results: list[tuple[str, str]], fmt: str) -> str:
    """Format results for output."""
    if fmt == "md":
        lines = ["# Document Summaries\n"]
        for name, summary in results:
            lines.append(f"## {name}\n\n{summary}\n")
        return "\n".join(lines)
    else:
        lines = []
        for name, summary in results:
            lines.append(f"{'='*60}\n{name}\n{'='*60}\n{summary}\n")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Batch summarize documents with Claude")
    parser.add_argument("path", help="File or directory to summarize")
    parser.add_argument("--style", choices=["bullet", "paragraph", "tldr"], default="bullet",
                        help="Summary style (default: bullet)")
    parser.add_argument("--format", choices=["text", "md"], default="text", dest="fmt",
                        help="Output format (default: text)")
    parser.add_argument("--output", "-o", help="Save to file instead of printing")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    target = Path(args.path)
    results = process_path(target, args.style, args.fmt)

    if not results:
        print("No files processed.")
        sys.exit(1)

    output = format_output(results, args.fmt)

    if args.output:
        Path(args.output).write_text(output)
        print(f"\nSaved to: {args.output}")
    else:
        print("\n" + output)

    print(f"\nDone. Summarized {len(results)} file(s).")


if __name__ == "__main__":
    main()

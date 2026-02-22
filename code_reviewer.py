#!/usr/bin/env python3
"""
code_reviewer.py — Automated code review using Claude.

Usage:
    python code_reviewer.py myfile.py
    python code_reviewer.py ./src/ --focus security
    python code_reviewer.py app.js --focus performance --output review.md
"""

import argparse
import os
import sys
from pathlib import Path

import anthropic

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".c", ".cpp", ".h", ".cs", ".rb", ".php", ".swift", ".kt"
}

client = anthropic.Anthropic()

REVIEW_PROMPTS = {
    "general": """Review this code and provide:
1. **Critical Issues** — bugs, security holes, crashes waiting to happen
2. **Code Quality** — readability, maintainability, best practices
3. **Improvements** — specific, actionable suggestions with examples
4. **Positives** — what's done well (be honest, skip if nothing stands out)

Be direct and specific. Reference line numbers where relevant.""",

    "security": """Security-focused code review. Check for:
1. **Injection vulnerabilities** (SQL, command, XSS, etc.)
2. **Authentication/authorization flaws**
3. **Sensitive data exposure** (logs, errors, hardcoded secrets)
4. **Input validation gaps**
5. **Dependency risks**

Rate severity: CRITICAL / HIGH / MEDIUM / LOW for each finding.""",

    "performance": """Performance-focused code review. Identify:
1. **Bottlenecks** — O(n²) loops, unnecessary DB calls, blocking I/O
2. **Memory issues** — leaks, excessive allocation, inefficient data structures
3. **Caching opportunities**
4. **Async/concurrency improvements**

Estimate impact: HIGH / MEDIUM / LOW for each finding.""",

    "tests": """Review this code for testability and test coverage:
1. **Untested paths** — what's missing coverage
2. **Hard-to-test patterns** — tight coupling, side effects, globals
3. **Suggested test cases** — specific scenarios to cover
4. **Testing improvements** — better assertions, fixtures, mocks""",
}


def read_code_file(path: Path) -> str | None:
    if path.suffix.lower() not in CODE_EXTENSIONS:
        print(f"  [skip] {path.name} — not a recognized code file")
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [error] {path.name}: {e}")
        return None


def review_code(content: str, filename: str, focus: str) -> str:
    prompt_instruction = REVIEW_PROMPTS.get(focus, REVIEW_PROMPTS["general"])

    prompt = f"""Code file: {filename}

{prompt_instruction}

```
{content[:10000]}
```"""

    if len(content) > 10000:
        prompt += f"\n\n[Note: File truncated — {len(content)} chars total, showing first 10000]"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main():
    parser = argparse.ArgumentParser(description="AI code review with Claude")
    parser.add_argument("path", help="File or directory to review")
    parser.add_argument("--focus", choices=["general", "security", "performance", "tests"],
                        default="general", help="Review focus (default: general)")
    parser.add_argument("--output", "-o", help="Save review to file")
    parser.add_argument("--ext", help="Extra extensions to include (comma-separated, e.g. .vue,.svelte)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    if args.ext:
        for ext in args.ext.split(","):
            CODE_EXTENSIONS.add(ext.strip() if ext.strip().startswith(".") else f".{ext.strip()}")

    target = Path(args.path)
    results = []

    if target.is_file():
        content = read_code_file(target)
        if content:
            print(f"Reviewing: {target.name} (focus: {args.focus})...")
            review = review_code(content, target.name, args.focus)
            results.append((target.name, review))

    elif target.is_dir():
        files = sorted(p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in CODE_EXTENSIONS)
        # Skip common noise
        files = [f for f in files if not any(part in f.parts for part in
                 ("node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"))]

        if not files:
            print(f"No code files found in {target}")
            sys.exit(1)

        print(f"Found {len(files)} files. Reviewing with focus: {args.focus}...")
        for f in files:
            content = read_code_file(f)
            if content:
                print(f"  Reviewing: {f.name}...")
                review = review_code(content, str(f.relative_to(target)), args.focus)
                results.append((str(f.relative_to(target)), review))
    else:
        print(f"Error: {target} not found")
        sys.exit(1)

    if not results:
        print("Nothing to review.")
        sys.exit(1)

    # Format output
    lines = [f"# Code Review — {args.focus.upper()}\n"]
    for name, review in results:
        lines.append(f"## {name}\n\n{review}\n\n---\n")
    output = "\n".join(lines)

    if args.output:
        Path(args.output).write_text(output)
        print(f"\nReview saved to: {args.output}")
    else:
        print("\n" + output)

    print(f"\nReviewed {len(results)} file(s).")


if __name__ == "__main__":
    main()

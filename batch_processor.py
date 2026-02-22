#!/usr/bin/env python3
"""
batch_processor.py — Run any Claude prompt against many inputs in parallel.

Usage:
    python batch_processor.py --prompt "translate to Spanish: {input}" --input words.txt
    python batch_processor.py --prompt "classify sentiment: {input}" --input tweets.txt --workers 5
    python batch_processor.py --template classify.txt --input items.txt --output results.csv
"""

import argparse
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic

client = anthropic.Anthropic()


def process_item(prompt_template: str, item: str, model: str, max_tokens: int) -> tuple[str, str]:
    """Process a single item. Returns (input, output)."""
    prompt = prompt_template.replace("{input}", item).replace("{INPUT}", item)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return item, response.content[0].text.strip()
    except anthropic.RateLimitError:
        time.sleep(5)
        # Retry once
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return item, response.content[0].text.strip()
        except Exception as e:
            return item, f"ERROR: {e}"
    except Exception as e:
        return item, f"ERROR: {e}"


def load_inputs(path: Path) -> list[str]:
    """Load inputs, one per line. Skips empty lines and comments."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]


def save_results(results: list[tuple[str, str]], output_path: Path, fmt: str) -> None:
    """Save results to file."""
    if fmt == "csv":
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["input", "output"])
            writer.writerows(results)
    elif fmt == "json":
        import json
        data = [{"input": r[0], "output": r[1]} for r in results]
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        lines = []
        for inp, out in results:
            lines.append(f"INPUT: {inp}\nOUTPUT: {out}\n{'─'*40}")
        output_path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Batch process inputs with Claude")
    parser.add_argument("--prompt", "-p", help="Prompt template with {input} placeholder")
    parser.add_argument("--template", "-t", help="File containing prompt template")
    parser.add_argument("--input", "-i", required=True, help="Input file (one item per line)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", choices=["text", "csv", "json"], default="text",
                        help="Output format (default: text)")
    parser.add_argument("--workers", "-w", type=int, default=3,
                        help="Parallel workers (default: 3, max: 10)")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001",
                        help="Model to use (default: haiku for speed/cost)")
    parser.add_argument("--max-tokens", type=int, default=256,
                        help="Max tokens per response (default: 256)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Get prompt template
    if args.template:
        prompt_template = Path(args.template).read_text(encoding="utf-8").strip()
    elif args.prompt:
        prompt_template = args.prompt
    else:
        print("Error: provide --prompt or --template")
        sys.exit(1)

    if "{input}" not in prompt_template.lower():
        print("Warning: prompt template has no {input} placeholder — same prompt will run for all inputs")

    # Load inputs
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    inputs = load_inputs(input_path)
    if not inputs:
        print("No inputs found")
        sys.exit(1)

    workers = min(args.workers, 10)
    print(f"Processing {len(inputs)} items with {workers} workers (model: {args.model})...\n")

    results = []
    errors = 0
    start = time.monotonic()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_item, prompt_template, item, args.model, args.max_tokens): item
            for item in inputs
        }

        for i, future in enumerate(as_completed(futures), 1):
            item, output = future.result()
            results.append((item, output))

            status = "ERROR" if output.startswith("ERROR:") else "OK"
            if status == "ERROR":
                errors += 1
            print(f"[{i}/{len(inputs)}] {status}: {item[:50]}")

    elapsed = time.monotonic() - start
    print(f"\nDone: {len(results)} processed, {errors} errors, {elapsed:.1f}s")

    # Preserve original order
    input_order = {item: i for i, item in enumerate(inputs)}
    results.sort(key=lambda r: input_order.get(r[0], 9999))

    if args.output:
        output_path = Path(args.output)
        save_results(results, output_path, args.format)
        print(f"Results saved to: {output_path}")
    else:
        for inp, out in results:
            print(f"\n--- {inp} ---")
            print(out)


if __name__ == "__main__":
    main()

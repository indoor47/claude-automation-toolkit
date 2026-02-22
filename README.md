# Claude Automation Toolkit

**5 production-ready Python scripts for automating real work with Claude AI.**

No fluff. No wrappers. Just scripts you can run today.

---

## What's Included

### 1. `summarize_docs.py` — Batch Document Summarizer
Summarize entire folders in seconds. Supports txt, md, py, js, json, csv, yaml, html + PDF.
```bash
python summarize_docs.py ./docs/ --style bullet --format md --output summary.md
python summarize_docs.py report.pdf --style paragraph
```

### 2. `code_reviewer.py` — AI Code Reviewer
Four focus modes: **general**, **security**, **performance**, **tests**.
```bash
python code_reviewer.py ./src/ --focus security --output review.md
python code_reviewer.py app.py --focus performance
```

### 3. `email_drafter.py` — Professional Email Drafter
Turn a sentence into a polished email. 5 tones, 6 templates, interactive refinement.
```bash
python email_drafter.py "ask client for extension, be friendly" --tone friendly
python email_drafter.py --interactive
```

### 4. `data_analyzer.py` — Natural Language Data Analyst
Ask plain English questions about CSV/JSON data. Interactive Q&A with memory.
```bash
python data_analyzer.py sales.csv "which region has highest churn?"
python data_analyzer.py metrics.json --interactive
```

### 5. `chat_with_files.py` — Document Chat
Load folders, files, or codebases and chat about them. 100k char context.
```bash
python chat_with_files.py ./codebase/ --filter "*.py"
python chat_with_files.py contract.pdf spec.md -q "what are the payment terms?"
```

### Bonus: `batch_processor.py` — Parallel Batch Processor
Run any Claude prompt against 1000 inputs in parallel. CSV/JSON/text output.
```bash
python batch_processor.py --prompt "classify sentiment: {input}" \
  --input reviews.txt --output results.csv --format csv --workers 5
```

---

## Setup

```bash
pip install anthropic           # required
pip install pypdf2 pandas       # optional: PDF + data analysis

export ANTHROPIC_API_KEY=your_key_here
```

Get your API key: https://console.anthropic.com

## Requirements

- Python 3.9+
- `ANTHROPIC_API_KEY` environment variable

## Cost Estimates

Scripts default to Haiku (cheapest). Approximate costs:
- Summarize 100 docs: ~$0.05–0.15
- Code review a 1000-line file: ~$0.02–0.05
- 1000 batch items: ~$0.10–0.30

## Support

If this saved you time, tips are welcome: `0xa8a0c1f762b31b4d71c88c0b65f33faae6d068bd` (ETH/ERC-20)

## License

MIT — use freely, modify, share, build on it.

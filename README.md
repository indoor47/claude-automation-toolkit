# Claude Automation Toolkit

Python scripts that automate real work with the Claude API. No wrappers, no frameworks, no boilerplate. Just scripts you can read, understand, and run.

## Free Tool: `summarize_docs.py`

Batch-summarize an entire folder of documents in one command. Supports txt, md, py, js, json, csv, yaml, html, and PDF (with pypdf2).

Three summary styles. Output to terminal or file. Works on single files or recursively through directories.

```bash
# Summarize a folder of docs as bullet points
python summarize_docs.py ./docs/ --style bullet --format md --output summary.md

# Quick paragraph summary of a single PDF
python summarize_docs.py report.pdf --style paragraph

# One-liner TL;DR
python summarize_docs.py notes.txt --style tldr
```

### Setup

```bash
pip install anthropic
pip install pypdf2    # optional, for PDF support

export ANTHROPIC_API_KEY=your_key_here
```

Get your API key at [console.anthropic.com](https://console.anthropic.com).

Requires Python 3.9+.

### Cost

Runs on Claude Haiku by default. Summarizing 100 documents costs roughly $0.05-0.15.

---

## Full Toolkit (6 Tools)

The free summarizer is one of six scripts in the complete toolkit. The paid version includes:

**AI Code Reviewer** -- Run security, performance, and test-focused code reviews from the command line. Point it at a file or directory, pick a focus mode, get a structured review.

**Email Drafter** -- Turn a one-line description into a polished email. Five tones, six templates, interactive refinement mode for when you need to iterate.

**Data Analyzer** -- Ask plain English questions about CSV and JSON files. Interactive session with memory so follow-up questions actually work.

**Document Chat** -- Load a folder, codebase, or collection of files and have a conversation about them. Handles up to 100k characters of context.

**Batch Processor** -- Run any Claude prompt against hundreds or thousands of inputs in parallel. CSV, JSON, or text output. Configurable concurrency.

All six scripts are readable Python. No dependencies beyond `anthropic` (and optional `pypdf2`/`pandas`). Your API key, your machine, your data. Nothing phones home.

**[Get the full toolkit](PURCHASE_LINK)** -- $19, one-time purchase.

---

## Support

Questions or issues with the free tool? Open an issue on this repo.

For the paid toolkit: support included with purchase.

## License

`summarize_docs.py` (this repo) is MIT licensed. The full toolkit is licensed per-purchase.

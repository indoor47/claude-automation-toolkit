#!/usr/bin/env python3
"""
email_drafter.py — Draft professional emails from bullet points using Claude.

Usage:
    python email_drafter.py "ask client for project extension, deadline is Friday, be friendly"
    python email_drafter.py --tone formal --context "B2B SaaS company" "follow up on unpaid invoice"
    echo "decline job offer politely" | python email_drafter.py -
"""

import argparse
import os
import sys

import anthropic

client = anthropic.Anthropic()

TONES = {
    "professional": "professional and polished, warm but not casual",
    "formal": "formal and respectful, appropriate for legal/financial/executive contexts",
    "friendly": "friendly and conversational, while still being professional",
    "assertive": "direct and assertive, clearly stating needs without being rude",
    "apologetic": "sincere and apologetic, taking accountability while remaining solution-focused",
}

TEMPLATES = {
    "followup": "This is a follow-up email to check on a previous message or meeting.",
    "request": "This email makes a specific request or ask.",
    "decline": "This email politely declines an offer, request, or invitation.",
    "intro": "This is an introduction email to make a first contact.",
    "complaint": "This email raises a concern or complaint professionally.",
    "thanks": "This is a thank-you email.",
}


def draft_email(
    intent: str,
    tone: str = "professional",
    context: str = "",
    template: str = "",
    recipient: str = "",
    sender: str = "",
) -> dict:
    """Draft an email using Claude. Returns subject and body."""

    tone_desc = TONES.get(tone, TONES["professional"])
    template_note = TEMPLATES.get(template, "")

    parts = [
        f"Draft a {tone_desc} email based on this intent:\n{intent}",
    ]

    if template_note:
        parts.append(f"Email type: {template_note}")
    if context:
        parts.append(f"Context: {context}")
    if recipient:
        parts.append(f"Recipient: {recipient}")
    if sender:
        parts.append(f"From: {sender}")

    parts.append(
        "\nRespond in this exact format:\n"
        "SUBJECT: [subject line here]\n\n"
        "BODY:\n[email body here]"
    )

    prompt = "\n\n".join(parts)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text

    # Parse subject and body
    subject = ""
    body = text

    if "SUBJECT:" in text:
        lines = text.split("\n")
        subject_line = next((l for l in lines if l.startswith("SUBJECT:")), "")
        subject = subject_line.replace("SUBJECT:", "").strip()

        # Find body after "BODY:"
        if "BODY:" in text:
            body_start = text.index("BODY:") + len("BODY:")
            body = text[body_start:].strip()

    return {"subject": subject, "body": body, "full": text}


def interactive_mode():
    """Interactive multi-draft mode."""
    print("Email Drafter — Interactive Mode")
    print("Type 'quit' to exit, 'new' to start a new email\n")

    while True:
        intent = input("What do you want to say? > ").strip()
        if intent.lower() in ("quit", "exit", "q"):
            break
        if not intent:
            continue

        tone = input("Tone [professional/formal/friendly/assertive/apologetic] (enter to skip): ").strip()
        tone = tone if tone in TONES else "professional"

        context = input("Any context to add? (enter to skip): ").strip()

        print("\nDrafting...\n")
        result = draft_email(intent, tone=tone, context=context)

        print(f"Subject: {result['subject']}\n")
        print(result["body"])

        refine = input("\nRefine this? (enter what to change, or 'done' to accept): ").strip()
        if refine and refine.lower() != "done":
            print("\nRefining...\n")
            refined = draft_email(
                f"Refine this email: {refine}\n\nOriginal email:\n{result['body']}",
                tone=tone,
                context=context,
            )
            print(f"Subject: {refined['subject']}\n")
            print(refined["body"])

        print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Draft professional emails with Claude")
    parser.add_argument("intent", nargs="?", help="What you want to say (use '-' for stdin)")
    parser.add_argument("--tone", choices=list(TONES.keys()), default="professional",
                        help="Email tone (default: professional)")
    parser.add_argument("--context", "-c", default="", help="Additional context")
    parser.add_argument("--template", "-t", choices=list(TEMPLATES.keys()),
                        help="Email template type")
    parser.add_argument("--to", dest="recipient", default="", help="Recipient name/role")
    parser.add_argument("--from", dest="sender", default="", help="Sender name/role")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive multi-draft mode")
    parser.add_argument("--output", "-o", help="Save to file")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    if args.interactive:
        interactive_mode()
        return

    # Get intent
    if args.intent == "-":
        intent = sys.stdin.read().strip()
    elif args.intent:
        intent = args.intent
    else:
        parser.print_help()
        sys.exit(1)

    print(f"Drafting email (tone: {args.tone})...\n")

    result = draft_email(
        intent,
        tone=args.tone,
        context=args.context,
        template=args.template or "",
        recipient=args.recipient,
        sender=args.sender,
    )

    output_text = f"Subject: {result['subject']}\n\n{result['body']}"

    if args.output:
        from pathlib import Path
        Path(args.output).write_text(output_text)
        print(f"Saved to: {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()

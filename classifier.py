import json
import os
import re
import time

import requests

MIN_CONFIDENCE = 0.8

SYSTEM_PROMPT = """You label emails that sit in a Gmail Spam folder.
Decide if each one is junk (should be trashed) or keep (a real message wrongly filed as spam).
junk = unsolicited promotion, adult or dating bait, scams, phishing, mass marketing.
keep = a real personal or transactional message (a real person, an order, a bank, a school, a receipt).
When unsure, answer keep.
Reply with only JSON, nothing else: {"label": "junk" or "keep", "confidence": a number from 0 to 1, "reason": "at most 12 words"}"""


def _keep(reason: str) -> dict:
    return {"label": "keep", "confidence": 0.0, "reason": reason, "trash": False}


def _parse(text: str) -> dict:
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        raise ValueError("no JSON in model reply")
    data = json.loads(match.group(0))

    label = str(data.get("label", "keep")).strip().lower()
    if label not in ("junk", "keep"):
        label = "keep"
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0))))
    except (TypeError, ValueError):
        confidence = 0.0
    reason = str(data.get("reason", ""))[:120]

    return {
        "label": label,
        "confidence": confidence,
        "reason": reason,
        "trash": label == "junk" and confidence >= MIN_CONFIDENCE,
    }


def classify_message(sender: str, subject: str, snippet: str = "") -> dict:

    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    api_key = os.getenv("LLM_API_KEY")
    if not (base_url and model and api_key):
        return _keep("model not configured")

    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 400,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Sender: {sender or ''}\nSubject: {subject or ''}\nSnippet: {(snippet or '')[:200]}",
            },
        ],
    }
    effort = os.getenv("LLM_REASONING_EFFORT")
    if effort:
        payload["reasoning_effort"] = effort

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = base_url.rstrip("/") + "/chat/completions"

    for attempt in range(2):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 429 and attempt == 0:
                time.sleep(3)
                continue
            res.raise_for_status()
            text = res.json()["choices"][0]["message"]["content"]
            return _parse(text)
        except Exception as e:
            if attempt == 1:
                return _keep(f"model error: {type(e).__name__}")
    return _keep("model error")


if __name__ == "__main__":
    # Quick test:  python classifier.py
    from dotenv import load_dotenv

    load_dotenv()
    samples = [
        ("FlirtNow <oeryujt@dicemak.example>", "I want to be a fantasy lady for you.", ""),
        ("FUTO Registry <registry@futo.edu.ng>", "Course registration deadline extended", ""),
        ("Bank Alerts <alerts@examplebank.com>", "Your account statement is ready", ""),
        ("Prize Center <win@claim-now.example>", "You have been selected for a free iPhone", ""),
    ]
    for sender, subject, snippet in samples:
        print(sender, "|", subject)
        print("   ->", classify_message(sender, subject, snippet))
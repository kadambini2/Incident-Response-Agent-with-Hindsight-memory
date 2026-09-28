"""Incident response agent: recall from Hindsight -> diagnose with Groq LLM."""
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

import memory

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
_llm = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")

SYSTEM = (
    "You are an on-call incident response assistant. Given a new alert, give: "
    "1) Likely root cause, 2) Recommended fix steps, 3) Confidence (low/medium/high). "
    "If past incidents are provided, base your answer on them and cite them by incident ID. "
    "Prefer fixes marked WORKED and avoid fixes marked FAILED. "
    "If no relevant history is provided, say the advice is generic."
)


def _chat(messages, retries: int = 3) -> str:
    last = None
    for attempt in range(retries):
        try:
            r = _llm.chat.completions.create(model=MODEL, messages=messages, temperature=0.2)
            return r.choices[0].message.content
        except Exception as e:  # rate limits / tool-format errors on free tier
            last = e
            time.sleep(1.5 * (attempt + 1))
    return f"LLM unavailable after {retries} attempts: {last}"


def diagnose(alert: str, use_memory: bool = True) -> dict:
    """Return {'answer': str, 'memories': list[str]}."""
    memories: list[str] = []
    if use_memory:
        try:
            memories = memory.recall_similar(alert)
        except Exception as e:
            memories = []
            alert += f"\n(Note: memory recall failed: {e})"

    if memories:
        history = "\n\n".join(f"[Past record {i+1}]\n{m}" for i, m in enumerate(memories))
        user = f"NEW ALERT:\n{alert}\n\nRELEVANT PAST INCIDENTS:\n{history}"
    else:
        user = f"NEW ALERT:\n{alert}\n\n(No past incident history available.)"

    answer = _chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
    return {"answer": answer, "memories": memories}

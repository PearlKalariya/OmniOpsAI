"""LLM answer generation over retrieved chunks, via LiteLLM.

LiteLLM is the gateway layer from the blueprint: model is configured by
name (provider/model), so swapping providers or adding routing later is a
config change, not a code change. Default model is Anthropic Claude Opus 4.8.
"""

import json
import re

import litellm

from app.core.config import settings

SYSTEM_PROMPT = (
    "You are OmniOps AI, an assistant that answers questions about the user's "
    "uploaded documents. Answer using ONLY the numbered context passages "
    "provided. Cite the passages you used as [1], [2], etc. If the context "
    "does not contain the answer, say so plainly — do not invent information."
)


def is_configured() -> bool:
    return bool(settings.llm_api_key)


def generate_answer(question: str, chunks: list[dict]) -> dict:
    """Build a grounded prompt from retrieved chunks and ask the LLM.

    Returns {"answer": str, "model": str}. Raises on provider errors —
    the route translates those to HTTP responses.
    """
    context = "\n\n".join(
        f"[{i + 1}] {chunk['content']}" for i, chunk in enumerate(chunks)
    )
    user_message = f"Context passages:\n\n{context}\n\nQuestion: {question}"

    response = litellm.completion(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    return {
        "answer": response.choices[0].message.content,
        "model": response.model,
    }


def complete_json(system: str, user: str, max_tokens: int = 512) -> dict:
    """One-shot completion that must return a JSON object.

    Extracts the first {...} block from the reply (models often wrap JSON
    in prose or code fences). Raises ValueError if no parseable object.
    """
    response = litellm.completion(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    text = response.choices[0].message.content or ""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object in LLM reply: {text[:200]!r}")
    return json.loads(match.group(0))

"""Shared Gemini async helper with retry and automatic model fallback."""
from __future__ import annotations

import asyncio

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from config import GEMINI_API_KEY, GEMINI_FALLBACK_MODEL, GEMINI_LLM_MODEL

_RETRY_DELAYS = [5, 15, 30]  # seconds; after these are exhausted, switch model


async def _call(client: genai.Client, model: str, prompt: str, temperature: float) -> str:
    response = await client.aio.models.generate_content(
        model=model,
        contents=[prompt],
        config=genai_types.GenerateContentConfig(temperature=temperature),
    )
    return response.text


async def generate(prompt: str, temperature: float = 0.3) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Try primary model with retries, then fall back to secondary model.
    for model, label in [(GEMINI_LLM_MODEL, "primary"), (GEMINI_FALLBACK_MODEL, "fallback")]:
        delays = _RETRY_DELAYS if label == "primary" else [5, 15]
        for attempt, delay in enumerate([0] + delays, start=1):
            if delay:
                await asyncio.sleep(delay)
            try:
                return await _call(client, model, prompt, temperature)
            except genai_errors.ServerError as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    if attempt <= len(delays):
                        print(
                            f"  [llm] {model} unavailable, retry {attempt}/{len(delays)} in {delays[attempt - 1]}s...",
                            flush=True,
                        )
                    else:
                        print(f"  [llm] {model} exhausted, switching to {GEMINI_FALLBACK_MODEL}...", flush=True)
                else:
                    raise
            except Exception:
                raise

    raise RuntimeError(
        f"Both {GEMINI_LLM_MODEL} and {GEMINI_FALLBACK_MODEL} are unavailable. Try again later."
    )

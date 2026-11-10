"""Thin wrapper around the Groq and Gemini chat APIs.

Settings come from environment variables (see .env.example):
    LLM_PROVIDER   groq or gemini
    GROQ_API_KEY / GROQ_MODEL
    GEMINI_API_KEY / GEMINI_MODEL
"""

import os

import requests

try:  # load a local .env file if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

TIMEOUT_SECONDS = 30
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class LLMError(Exception):
    """Raised when the LLM provider is misconfigured or a request fails."""


def _require_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise LLMError(f"{name} is not set. Add it to your .env file.")
    return value


def _post(url, headers, payload):
    """POST JSON and return the decoded reply, or raise LLMError.

    Error messages never include headers, so the API key cannot leak.
    """
    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as error:
        raise LLMError("The LLM provider timed out") from error
    except requests.exceptions.HTTPError as error:
        status = error.response.status_code if error.response is not None else "?"
        raise LLMError(f"The LLM provider returned HTTP {status}") from error
    except (requests.exceptions.RequestException, ValueError) as error:
        raise LLMError("Could not reach the LLM provider") from error


def _groq(system_prompt, user_prompt, temperature):
    data = _post(
        GROQ_URL,
        {"Authorization": f"Bearer {_require_env('GROQ_API_KEY')}"},
        {
            "model": _require_env("GROQ_MODEL"),
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
    )
    return data["choices"][0]["message"]["content"]


def _gemini(system_prompt, user_prompt, temperature):
    model = _require_env("GEMINI_MODEL")
    data = _post(
        GEMINI_URL.format(model=model),
        {"x-goog-api-key": _require_env("GEMINI_API_KEY")},
        {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": temperature},
        },
    )
    return data["candidates"][0]["content"]["parts"][0]["text"]


PROVIDERS = {"groq": _groq, "gemini": _gemini}


def complete(system_prompt, user_prompt, temperature=0.2):
    """Send a system + user prompt to the configured provider; return text."""
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    if provider not in PROVIDERS:
        raise LLMError(f"Unknown LLM_PROVIDER '{provider}'. Use groq or gemini.")
    try:
        return PROVIDERS[provider](system_prompt, user_prompt, temperature)
    except (KeyError, IndexError, TypeError) as error:
        raise LLMError("Unexpected reply format from the LLM provider") from error

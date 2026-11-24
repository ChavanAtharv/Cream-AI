"""Thin wrapper around the Groq and Gemini chat APIs.

Settings come from environment variables (see .env.example):
    LLM_PROVIDER   groq or gemini
    GROQ_API_KEY / GROQ_MODEL
    GEMINI_API_KEY / GEMINI_MODEL
"""

import logging
import os

import requests

logger = logging.getLogger("schemesaathi.llm")

try:  # load a local .env file if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

TIMEOUT_SECONDS = 30
# gpt-oss models on Groq sometimes try to call a tool that does not exist;
# the request fails with this message and usually works if sent again.
TOOL_CALL_ERROR = "Tool choice is none"
ATTEMPTS = 3
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
        message = f"The LLM provider returned HTTP {status}"
        try:  # the provider usually explains what was wrong
            reason = str(error.response.json()["error"]["message"])[:200]
            message += f": {reason}"
        except (AttributeError, KeyError, TypeError, ValueError):
            pass
        raise LLMError(message) from error
    except (requests.exceptions.RequestException, ValueError) as error:
        raise LLMError("Could not reach the LLM provider") from error


def _groq(system_prompt, user_prompt, temperature):
    configured_model = _require_env("GROQ_MODEL")
    candidate_models = [configured_model]
    for fallback in ("llama-3.1-8b-instant", "openai/gpt-oss-20b", "llama3-8b-8192"):
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error = None
    for model_name in candidate_models:
        try:
            data = _post(
                GROQ_URL,
                {"Authorization": f"Bearer {_require_env('GROQ_API_KEY')}"},
                {
                    "model": model_name,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            usage = data.get("usage")
            if usage and isinstance(usage, dict):
                logger.info(
                    "[TOKEN_USAGE] provider=groq model=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
                    model_name,
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    usage.get("total_tokens"),
                )
            return data["choices"][0]["message"]["content"]
        except LLMError as err:
            err_str = str(err)
            if (
                "HTTP 404" in err_str
                or "does not exist" in err_str
                or "not have access" in err_str
            ):
                logger.warning(
                    "Groq model '%s' unavailable (%s). Falling back to next candidate model.",
                    model_name,
                    err,
                )
                last_error = err
                continue
            raise
    if last_error:
        raise last_error


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
    usage = data.get("usageMetadata")
    if usage and isinstance(usage, dict):
        logger.info(
            "[TOKEN_USAGE] provider=gemini model=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            model,
            usage.get("promptTokenCount"),
            usage.get("candidatesTokenCount"),
            usage.get("totalTokenCount"),
        )
    return data["candidates"][0]["content"]["parts"][0]["text"]


PROVIDERS = {"groq": _groq, "gemini": _gemini}


def complete(system_prompt, user_prompt, temperature=0.2):
    """Send a system + user prompt to the configured provider; return text."""
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    if provider not in PROVIDERS:
        raise LLMError(f"Unknown LLM_PROVIDER '{provider}'. Use groq or gemini.")
    for attempt in range(ATTEMPTS):
        try:
            return PROVIDERS[provider](system_prompt, user_prompt, temperature)
        except (KeyError, IndexError, TypeError) as error:
            raise LLMError("Unexpected reply format from the LLM provider") from error
        except LLMError as error:
            if TOOL_CALL_ERROR in str(error) and attempt < ATTEMPTS - 1:
                continue
            raise

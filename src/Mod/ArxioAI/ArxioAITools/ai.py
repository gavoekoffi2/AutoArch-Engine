# SPDX-License-Identifier: LGPL-2.1-or-later
"""LLM client for Arxio AI.

Zero third-party dependencies — only `urllib` from the Python stdlib
so no pip install is required for users.

Supported providers:
    - "anthropic" (default) — Messages API
    - "openai"              — Chat Completions API (and compatible
                              endpoints: Azure, groq, together, Ollama
                              via OpenAI shim, etc.)

The API key is never stored in source. It is read from, in order:

    1. The FreeCAD parameter store
       `User parameter:BaseApp/Preferences/Mod/ArxioAI` → `AIAPIKey`
    2. Environment variables `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
"""

import json
import os
import re
import urllib.error
import urllib.request

import FreeCAD


PREF_GROUP = "User parameter:BaseApp/Preferences/Mod/ArxioAI"


DEFAULTS = {
    "AIProvider": "anthropic",
    "AIBaseURL": "https://api.anthropic.com/v1",
    "AIModel": "claude-sonnet-4-5",
    "AIMaxTokens": 2048,
    "AITimeout": 60,
}


class LLMError(Exception):
    """Raised when the LLM call fails for any reason."""


# ---------------------------------------------------------------------------
# Config read / write
# ---------------------------------------------------------------------------
def _params():
    return FreeCAD.ParamGet(PREF_GROUP)


def get_config():
    p = _params()
    provider = p.GetString("AIProvider", DEFAULTS["AIProvider"])
    base_url = p.GetString("AIBaseURL", DEFAULTS["AIBaseURL"])
    model = p.GetString("AIModel", DEFAULTS["AIModel"])
    api_key = p.GetString("AIAPIKey", "")
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get(
            "OPENAI_API_KEY", ""
        )
    return {
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
        "max_tokens": p.GetInt("AIMaxTokens", DEFAULTS["AIMaxTokens"]),
        "timeout": p.GetInt("AITimeout", DEFAULTS["AITimeout"]),
    }


def set_config(**kwargs):
    p = _params()
    mapping = {
        "provider": ("SetString", "AIProvider"),
        "base_url": ("SetString", "AIBaseURL"),
        "model": ("SetString", "AIModel"),
        "api_key": ("SetString", "AIAPIKey"),
        "max_tokens": ("SetInt", "AIMaxTokens"),
        "timeout": ("SetInt", "AITimeout"),
    }
    for key, value in kwargs.items():
        if value is None or key not in mapping:
            continue
        method, param = mapping[key]
        getattr(p, method)(param, value)


def has_api_key():
    return bool(get_config()["api_key"])


# ---------------------------------------------------------------------------
# HTTP plumbing
# ---------------------------------------------------------------------------
def _http_json(url, headers, body, timeout):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"Erreur réseau : {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise LLMError(f"Erreur I/O : {exc}") from exc


def _chat_anthropic(messages, system, cfg):
    url = cfg["base_url"].rstrip("/") + "/messages"
    body = {
        "model": cfg["model"],
        "max_tokens": cfg["max_tokens"],
        "messages": messages,
    }
    if system:
        body["system"] = system
    headers = {
        "Content-Type": "application/json",
        "x-api-key": cfg["api_key"],
        "anthropic-version": "2023-06-01",
    }
    data = _http_json(url, headers, body, cfg["timeout"])
    blocks = data.get("content", []) or []
    return "\n".join(b.get("text", "") for b in blocks if b.get("type") == "text")


def _chat_openai(messages, system, cfg):
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    compiled = []
    if system:
        compiled.append({"role": "system", "content": system})
    compiled.extend(messages)
    body = {
        "model": cfg["model"],
        "messages": compiled,
        "max_tokens": cfg["max_tokens"],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    data = _http_json(url, headers, body, cfg["timeout"])
    choices = data.get("choices", [])
    if not choices:
        raise LLMError("Réponse vide du fournisseur OpenAI-compatible.")
    return choices[0].get("message", {}).get("content", "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def chat(messages, system=None, config=None):
    """Send `messages` (list of {role, content} dicts) to the LLM.

    Returns the assistant's text response.
    """
    cfg = config or get_config()
    if not cfg["api_key"]:
        raise LLMError(
            "Aucune clé API configurée. Menu Arxio AI → Intelligence → Configurer l'IA."
        )
    provider = (cfg["provider"] or "").lower()
    if provider == "anthropic":
        return _chat_anthropic(messages, system, cfg)
    if provider in ("openai", "openai-compatible"):
        return _chat_openai(messages, system, cfg)
    raise LLMError(f"Fournisseur inconnu : {cfg['provider']!r}")


def ask(prompt, system=None, config=None):
    """Convenience wrapper: one-shot user prompt → assistant text."""
    return chat([{"role": "user", "content": prompt}], system=system, config=config)


_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_json(text):
    """Pull the first JSON object out of a free-form LLM response."""
    match = _JSON_BLOCK_RE.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Fallback: first "{...}" span that parses.
    first = text.find("{")
    last = text.rfind("}")
    if 0 <= first < last:
        try:
            return json.loads(text[first : last + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"Réponse LLM non-JSON : {exc}") from exc
    raise LLMError("Aucun objet JSON trouvé dans la réponse de l'IA.")

import os
import logfire
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from groq import Groq

from app.config import settings


# Production gateway config:
GATEWAY_CONFIG = {
    "strategy": {"mode": "fallback"},
    "cache": {"mode": "simple"},
    "retry": {
        "attempts": 2,
        "on_status_codes": [429, 503]
    },
    "targets": [
        {"override_params": {"model": f"@{settings.GROQ_SLUG}/{settings.GROQ_MODEL}"}},
        {"override_params": {"model": f"@{settings.GROQ_SLUG_2}/{settings.GROQ_MODEL}"}},
    ]
}


class ResilientPortkeyCompletions:
    def __init__(self, raw_portkey: Portkey, primary_groq: Groq, fallback_groq: Groq | None):
        self._portkey = raw_portkey
        self._primary_groq = primary_groq
        self._fallback_groq = fallback_groq

    def create(self, **kwargs):
        """
        Attempts to call Portkey first. If Portkey encounters an authentication,
        configuration, or gateway error, it seamlessly fails over to direct Groq.
        """
        try:
            return self._portkey.chat.completions.create(**kwargs)
        except Exception as e:
            logfire.warning(f"⚠️ Portkey gateway call failed ({e}); failing over to direct Groq...")

        call_kwargs = dict(kwargs)
        call_kwargs["model"] = settings.GROQ_MODEL

        try:
            return self._primary_groq.chat.completions.create(**call_kwargs)
        except Exception as e_groq:
            logfire.warning(f"⚠️ Primary Groq key failed ({e_groq}); failing over to fallback Groq...")
            if self._fallback_groq:
                return self._fallback_groq.chat.completions.create(**call_kwargs)
            raise e_groq


class ResilientPortkeyChat:
    def __init__(self, completions: ResilientPortkeyCompletions):
        self.completions = completions


class ResilientPortkeyClient:
    def __init__(self):
        config_arg = os.getenv("PORTKEY_CONFIG_ID") or GATEWAY_CONFIG
        self._raw_portkey = Portkey(
            api_key=settings.PORTKEY_API_KEY,
            config=config_arg
        )
        self._primary_groq = Groq(api_key=settings.GROQ_API_KEY)
        self._fallback_groq = Groq(api_key=settings.GROQ_FALLBACK_API_KEY) if settings.GROQ_FALLBACK_API_KEY else None
        self.chat = ResilientPortkeyChat(
            ResilientPortkeyCompletions(self._raw_portkey, self._primary_groq, self._fallback_groq)
        )


portkey_client = ResilientPortkeyClient()


def get_langchain_llm(feature: str = "rag"):
    """
    Returns a resilient LLM runnable that routes through Portkey with
    automatic failover to primary and backup Groq models.
    """
    config_arg = os.getenv("PORTKEY_CONFIG_ID") or GATEWAY_CONFIG
    headers = createHeaders(
        api_key=settings.PORTKEY_API_KEY,
        config=config_arg,
        metadata={
            "feature": feature,
            "_user": "rag-system",
            "environment": "production"
        }
    )

    portkey_llm = ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model=f"@{settings.GROQ_SLUG}/{settings.GROQ_MODEL}",
        temperature=0,
        default_headers=headers
    )

    primary_groq = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0
    )

    fallback_models = [primary_groq]
    if settings.GROQ_FALLBACK_API_KEY:
        fallback_models.append(
            ChatGroq(
                api_key=settings.GROQ_FALLBACK_API_KEY,
                model=settings.GROQ_MODEL,
                temperature=0
            )
        )

    return portkey_llm.with_fallbacks(fallback_models)


def extract_cache_status(response) -> str:
    """
    Pull x-portkey-cache-status from the Portkey response headers.
    Returns 'MISS' if served directly via Groq or if not in cache.
    """
    for attr in ("_raw_response", "_response", "_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            status = getattr(raw, "headers", {}).get("x-portkey-cache-status", "")
            if status:
                return status.upper()
    return "MISS"

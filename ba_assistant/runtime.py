"""Refresh application-owned objects retained across Streamlit code reloads."""

from .models import SessionState
from .openrouter import FREE_MODEL, FreeProviderConfig, OpenRouter
from .session import Session
from .workflow import Workflow


def refresh_workflow(previous):
    provider = previous.provider
    config = getattr(provider, "config", None)
    if (type(provider).__module__ == "ba_assistant.openrouter"
            and type(provider).__name__ == "OpenRouter"
            and getattr(config, "model", None) in (FREE_MODEL, "inclusionai/ling-3.2-flash:free")):
        # Revalidate even old config/model objects using the current contracts.
        previous_provider = provider
        settings = config.model_dump()
        settings["model"] = FREE_MODEL
        provider = OpenRouter(FreeProviderConfig.model_validate(settings),
                              transport=provider.transport, sleep=provider.sleep)
        provider._schema_failure = getattr(previous_provider, "_schema_failure", None)
    session = Session()
    session._state = SessionState.model_validate(previous.session.state.model_dump())
    refreshed = Workflow(session, provider)
    refreshed._records = list(previous.records)
    return refreshed

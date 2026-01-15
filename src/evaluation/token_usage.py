"""
Token usage instrumentation (query-time).

Uses LlamaIndex callback handlers to collect (as accurately as possible):
- LLM prompt/completion/total tokens
- Embedding token usage (all embedding calls during answering)

This is best-effort across LlamaIndex versions: imports/attribute names may differ.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional, Tuple

import tiktoken


def _safe_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except Exception:
        return 0


def _build_token_counting_handler() -> Tuple[Optional[object], Optional[object]]:
    """
    Returns (callback_manager, handler) or (None, None) if unavailable.
    """
    try:
        from llama_index.core.callbacks import CallbackManager  # type: ignore
    except Exception:
        return (None, None)

    TokenCountingHandler = None
    try:
        from llama_index.core.callbacks import TokenCountingHandler  # type: ignore

        TokenCountingHandler = TokenCountingHandler
    except Exception:
        try:
            from llama_index.core.callbacks.token_counting import (  # type: ignore
                TokenCountingHandler as _TokenCountingHandler,
            )

            TokenCountingHandler = _TokenCountingHandler
        except Exception:
            TokenCountingHandler = None

    if TokenCountingHandler is None:
        return (None, None)

    # Tokenizer: use the common cl100k_base encoding (works for GPT-4/4o family)
    encoding = tiktoken.get_encoding("cl100k_base")
    tokenizer = encoding.encode

    try:
        handler = TokenCountingHandler(tokenizer=tokenizer)
    except TypeError:
        # Some versions use a different parameter name or accept no tokenizer.
        handler = TokenCountingHandler()

    try:
        callback_manager = CallbackManager([handler])
    except Exception:
        return (None, None)

    return (callback_manager, handler)


def _extract_counts(handler: object) -> Dict[str, Any]:
    """
    Convert handler state into a stable dict. Attribute names vary by version,
    so we probe multiple options.
    """
    llm_prompt = _safe_int(
        getattr(handler, "prompt_llm_token_count", None)
        or getattr(handler, "prompt_token_count", None)
        or getattr(handler, "prompt_tokens", None)
    )
    llm_completion = _safe_int(
        getattr(handler, "completion_llm_token_count", None)
        or getattr(handler, "completion_token_count", None)
        or getattr(handler, "completion_tokens", None)
    )
    llm_total = _safe_int(
        getattr(handler, "total_llm_token_count", None)
        or getattr(handler, "total_token_count", None)
        or getattr(handler, "total_tokens", None)
    )

    embed_total = _safe_int(
        getattr(handler, "total_embedding_token_count", None)
        or getattr(handler, "embedding_token_count", None)
        or getattr(handler, "embedding_tokens", None)
    )

    # Ensure totals are consistent even if handler doesn't expose them directly.
    if llm_total == 0 and (llm_prompt or llm_completion):
        llm_total = llm_prompt + llm_completion

    return {
        "llm": {
            "prompt_tokens": llm_prompt,
            "completion_tokens": llm_completion,
            "total_tokens": llm_total,
        },
        "embeddings": {"total_tokens": embed_total},
    }


@contextmanager
def token_usage_context() -> Iterator[callable]:
    """
    Context manager that installs a callback manager for LlamaIndex Settings
    and yields a callable that returns the final usage dict.

    If token counting isn't available, yields a callable returning zeros.
    """
    try:
        from llama_index.core import Settings  # type: ignore
    except Exception:
        yield lambda: {"llm": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, "embeddings": {"total_tokens": 0}}
        return

    callback_manager, handler = _build_token_counting_handler()
    if callback_manager is None or handler is None:
        yield lambda: {"llm": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, "embeddings": {"total_tokens": 0}}
        return

    old_cb = getattr(Settings, "callback_manager", None)
    try:
        Settings.callback_manager = callback_manager
        def _get_usage() -> Dict[str, Any]:
            return _extract_counts(handler)

        # Expose callback manager so callers can attach it to concrete LLM/embedding instances
        # that may not respect Settings.callback_manager.
        setattr(_get_usage, "callback_manager", callback_manager)
        yield _get_usage
    finally:
        try:
            Settings.callback_manager = old_cb
        except Exception:
            pass


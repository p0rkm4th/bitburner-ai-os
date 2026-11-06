"""Small durable cache for successful, allowlisted documentation lookups."""
import hashlib
import re


MAX_CACHED_QUERIES = 8
MAX_CACHED_RESULT = 3800
MAX_REPEAT_CONTEXT = 800


def _query_key(tool: str, query: str) -> str:
    normalized = re.sub(r"\s+", " ", query.strip()).casefold()
    # Hash the full normalized query: long runtime errors often differ only
    # after a shared prefix, so truncating the key can return unrelated advice.
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{tool}:{digest}"


def cached_query_result(action_state: dict, tool: str, query: str) -> str | None:
    cache = action_state.get("doc_query_cache", {})
    if not isinstance(cache, dict):
        return None
    result = cache.get(_query_key(tool, query))
    return result if isinstance(result, str) else None


def remember_query_result(action_state: dict, tool: str, query: str, result: str) -> None:
    if not isinstance(result, str) or not result or result.startswith("ERROR:"):
        return
    cache = action_state.setdefault("doc_query_cache", {})
    if not isinstance(cache, dict):
        cache = action_state["doc_query_cache"] = {}
    cache[_query_key(tool, query)] = result[:MAX_CACHED_RESULT]
    # Dict insertion order lets us retain the latest distinct lookups only.
    while len(cache) > MAX_CACHED_QUERIES:
        del cache[next(iter(cache))]


def doc_query_cache_checkpoint(action_state: dict) -> list[dict[str, str]]:
    cache = action_state.get("doc_query_cache", {})
    if not isinstance(cache, dict):
        return []
    return [{"key": str(key)[:240], "result": str(value)[:MAX_CACHED_RESULT]}
            for key, value in list(cache.items())[-MAX_CACHED_QUERIES:]
            if isinstance(key, str) and isinstance(value, str)]


def restore_doc_query_cache(checkpoint: dict, action_state: dict) -> None:
    stored = checkpoint.get("doc_query_cache")
    if not isinstance(stored, list):
        return
    cache = {}
    for item in stored[-MAX_CACHED_QUERIES:]:
        if not isinstance(item, dict):
            continue
        key, result = item.get("key"), item.get("result")
        if isinstance(key, str) and isinstance(result, str):
            cache[key[:240]] = result[:MAX_CACHED_RESULT]
    if cache:
        action_state["doc_query_cache"] = cache


def repeated_query_message(tool: str, result: str) -> str:
    return (f"NO_PROGRESS: This exact {tool} lookup already returned during this gameplay task. "
            "Do not repeat it; use the prior result below and take a different evidence-based action.\n"
            f"Prior result excerpt: {result[:MAX_REPEAT_CONTEXT]}")

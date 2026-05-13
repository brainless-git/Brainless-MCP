"""GraphQL client with rate limiting, caching, and connection pooling."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from ..config import get_settings
from .exceptions import UnraidAuthError, UnraidError, UnraidNotFoundError, UnraidRateLimitError

# ---------------------------------------------------------------------------
# Token-bucket rate limiter
# ---------------------------------------------------------------------------

class _TokenBucket:
    """Simple token-bucket for rate limiting."""

    def __init__(self, capacity: float, refill_rate: float) -> None:
        self._capacity = capacity
        self._tokens = capacity
        self._refill_rate = refill_rate
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            delta = now - self._last
            self._tokens = min(self._capacity, self._tokens + delta * self._refill_rate)
            self._last = now
            if self._tokens < 1:
                wait = (1 - self._tokens) / self._refill_rate
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1


# ---------------------------------------------------------------------------
# Query cache
# ---------------------------------------------------------------------------

class _QueryCache:
    def __init__(self, ttl: float = 60.0) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry and time.monotonic() - entry[0] < self._ttl:
            return entry[1]
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.monotonic(), value)

    def invalidate(self, prefix: str = "") -> None:
        if prefix:
            self._store = {k: v for k, v in self._store.items() if not k.startswith(prefix)}
        else:
            self._store.clear()


# ---------------------------------------------------------------------------
# GraphQL client
# ---------------------------------------------------------------------------

class UnraidClient:
    """Singleton async GraphQL client for the Unraid API."""

    _instance: "UnraidClient | None" = None

    def __new__(cls) -> "UnraidClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialised:
            return
        self._initialised = True
        settings = get_settings()
        self._settings = settings
        self._rate_limiter = _TokenBucket(capacity=90, refill_rate=9.0)
        self._cache = _QueryCache(ttl=60.0)
        self._http: httpx.AsyncClient | None = None

    def _build_http(self) -> httpx.AsyncClient:
        s = self._settings
        headers = {
            "Content-Type": "application/json",
            "x-api-key": s.unraid_api_key,
        }
        return httpx.AsyncClient(
            base_url=s.graphql_url,
            headers=headers,
            verify=s.ssl_verify,
            timeout=s.request_timeout,
            http2=False,
        )

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = self._build_http()
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
        self._http = None

    # ------------------------------------------------------------------
    # Core execute
    # ------------------------------------------------------------------

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        cache_key: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query/mutation and return the `data` dict."""
        if cache_key:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        await self._rate_limiter.acquire()
        http = await self._get_http()

        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            resp = await http.post(
                "",
                json=payload,
                timeout=timeout or self._settings.request_timeout,
            )
        except httpx.TimeoutException as exc:
            raise UnraidError(f"Request timed out: {exc}") from exc
        except httpx.ConnectError as exc:
            raise UnraidError(f"Cannot connect to Unraid at {self._settings.unraid_api_url}: {exc}") from exc

        if resp.status_code == 401:
            raise UnraidAuthError("Unraid API rejected the API key (HTTP 401).")
        if resp.status_code == 403:
            raise UnraidAuthError("Unraid API forbidden (HTTP 403). Check API key permissions.")
        if resp.status_code == 429:
            raise UnraidRateLimitError("Unraid API rate limit hit (HTTP 429).")
        if resp.status_code >= 500:
            raise UnraidError(f"Unraid server error (HTTP {resp.status_code}): {resp.text[:500]}")
        if resp.status_code >= 400:
            raise UnraidError(f"Unraid API error (HTTP {resp.status_code}): {resp.text[:500]}")

        body: dict[str, Any] = resp.json()

        if "errors" in body:
            errs = body["errors"]
            msg = errs[0].get("message", str(errs)) if errs else "Unknown GraphQL error"
            if "not found" in msg.lower():
                raise UnraidNotFoundError(msg)
            if "unauthorized" in msg.lower() or "forbidden" in msg.lower():
                raise UnraidAuthError(msg)
            raise UnraidError(f"GraphQL error: {msg}")

        data = body.get("data", {})
        if cache_key:
            self._cache.set(cache_key, data)
        return data

    async def query(self, gql: str, variables: dict[str, Any] | None = None, cache: bool = True) -> dict[str, Any]:
        """Execute a read-only query, optionally cached."""
        key = f"{gql[:80]}:{variables}" if cache else None
        return await self.execute(gql, variables, cache_key=key)

    async def mutate(self, gql: str, variables: dict[str, Any] | None = None, invalidate_prefix: str = "") -> dict[str, Any]:
        """Execute a mutation, invalidating relevant cache entries."""
        result = await self.execute(gql, variables)
        if invalidate_prefix:
            self._cache.invalidate(invalidate_prefix)
        else:
            self._cache.invalidate()
        return result

    async def disk_query(self, gql: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a query with the longer disk-operation timeout."""
        return await self.execute(gql, variables, timeout=self._settings.disk_op_timeout)

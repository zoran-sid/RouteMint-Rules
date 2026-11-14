"""HTTP fetching with an on-disk "last known good" snapshot.

A single flaky upstream must never empty a rule set, so every successful
download is cached.  If a later download fails the cached copy is reused and
the build report marks the category as degraded instead of shipping nothing.
"""

from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

USER_AGENT = "RouteMint-Rules/0.1 (+https://github.com/zoran-sid/RouteMint-Rules)"


class FetchError(Exception):
    """No network copy and no usable snapshot."""

    def __init__(self, message: str, *, url: str = "", status: int | None = None) -> None:
        super().__init__(message)
        self.url = url
        self.status = status


@dataclass
class FetchOutcome:
    url: str
    content: bytes
    fetched_at: datetime
    from_cache: bool
    stale: bool = False
    error: str | None = None

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", "replace")


@dataclass
class FetchStats:
    network: int = 0
    cache_hits: int = 0
    stale_hits: int = 0
    failures: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "network": self.network,
            "cache_hits": self.cache_hits,
            "stale_hits": self.stale_hits,
            "failures": self.failures,
        }


class Fetcher:
    def __init__(
        self,
        cache_dir: Path,
        *,
        timeout: float = 30.0,
        retries: int = 2,
        ttl_hours: float = 24.0,
        offline: bool = False,
        refresh: bool = False,
        max_workers: int = 16,
    ) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retries = retries
        self.ttl = timedelta(hours=ttl_hours)
        self.offline = offline
        self.refresh = refresh
        self.stats = FetchStats()
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"},
        )
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._mem: dict[str, FetchOutcome] = {}

    # -- public API -----------------------------------------------------
    def get(self, url: str) -> FetchOutcome:
        if url in self._mem:
            return self._mem[url]
        outcome = self._load(url)
        self._mem[url] = outcome
        return outcome

    def get_text(self, url: str) -> FetchOutcome:
        return self.get(url)

    def get_many(self, urls: list[str]) -> dict[str, FetchOutcome]:
        """Fetch concurrently; order of ``urls`` is preserved in the result."""
        missing = [u for u in dict.fromkeys(urls) if u not in self._mem]
        if missing:
            for url, outcome in zip(missing, self._pool.map(self.get, missing), strict=True):
                self._mem[url] = outcome
        return {u: self._mem[u] for u in urls}

    def close(self) -> None:
        self._client.close()
        self._pool.shutdown(wait=False)

    def __enter__(self) -> "Fetcher":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- internals ------------------------------------------------------
    def _paths(self, url: str) -> tuple[Path, Path]:
        key = hashlib.sha256(url.encode()).hexdigest()[:20]
        return self.cache_dir / f"{key}.bin", self.cache_dir / f"{key}.json"

    def _read_cache(self, url: str) -> FetchOutcome | None:
        body, meta = self._paths(url)
        if not body.is_file():
            return None
        try:
            info = json.loads(meta.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(info["fetched_at"])
        except (OSError, ValueError, KeyError):
            fetched_at = datetime.fromtimestamp(body.stat().st_mtime, tz=UTC)
        return FetchOutcome(
            url=url,
            content=body.read_bytes(),
            fetched_at=fetched_at,
            from_cache=True,
        )

    def _write_cache(self, url: str, content: bytes, fetched_at: datetime) -> None:
        body, meta = self._paths(url)
        tmp = body.with_suffix(".tmp")
        tmp.write_bytes(content)
        tmp.replace(body)
        meta.write_text(
            json.dumps({"url": url, "fetched_at": fetched_at.isoformat(), "bytes": len(content)}),
            encoding="utf-8",
        )

    def _download(self, url: str) -> bytes:
        last_error: Exception | None = None
        status: int | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self._client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                # A 404 will not become a 200 by retrying.
                if 400 <= status < 500 and status != 429:
                    break
            except (httpx.HTTPError, OSError) as exc:
                last_error = exc
            if attempt < self.retries:
                time.sleep(1.5 * (attempt + 1))
        raise FetchError(f"{url}: {last_error}", url=url, status=status)

    def _load(self, url: str) -> FetchOutcome:
        cached = self._read_cache(url)
        now = datetime.now(tz=UTC)
        fresh = cached is not None and (now - cached.fetched_at) < self.ttl

        if self.offline or (cached is not None and fresh and not self.refresh):
            if cached is None:
                raise FetchError(f"{url}: offline and no snapshot")
            self.stats.cache_hits += 1
            return cached

        try:
            content = self._download(url)
        except FetchError as exc:
            if cached is not None:
                self.stats.stale_hits += 1
                self.stats.failures.append(str(exc))
                return FetchOutcome(
                    url=url,
                    content=cached.content,
                    fetched_at=cached.fetched_at,
                    from_cache=True,
                    stale=True,
                    error=str(exc),
                )
            self.stats.failures.append(str(exc))
            raise

        self.stats.network += 1
        self._write_cache(url, content, now)
        return FetchOutcome(url=url, content=content, fetched_at=now, from_cache=False)

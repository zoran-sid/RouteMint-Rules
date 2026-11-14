from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from builder.fetch import FetchError, Fetcher

RESPONSES: dict[str, bytes] = {}
STATUS: dict[str, int] = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        status = STATUS.get(self.path, 200)
        body = RESPONSES.get(self.path, b"")
        if status != 200:
            self.send_error(status)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture()
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    yield f"http://{host}:{port}"
    httpd.shutdown()
    thread.join(timeout=5)
    RESPONSES.clear()
    STATUS.clear()


def test_download_then_cache_hit(tmp_path: Path, server: str) -> None:
    RESPONSES["/list.txt"] = b"example.com\n"
    with Fetcher(tmp_path, ttl_hours=1) as fetcher:
        first = fetcher.get(f"{server}/list.txt")
        assert first.text == "example.com\n"
        assert first.from_cache is False
        assert fetcher.stats.network == 1

    with Fetcher(tmp_path, ttl_hours=1) as fetcher:
        second = fetcher.get(f"{server}/list.txt")
        assert second.from_cache is True
        assert second.stale is False
        assert fetcher.stats.cache_hits == 1


def test_failed_refresh_falls_back_to_snapshot(tmp_path: Path, server: str) -> None:
    url = f"{server}/list.txt"
    RESPONSES["/list.txt"] = b"example.com\n"
    with Fetcher(tmp_path, ttl_hours=1) as fetcher:
        fetcher.get(url)

    STATUS["/list.txt"] = 500
    with Fetcher(tmp_path, ttl_hours=0, refresh=True, retries=0) as fetcher:
        outcome = fetcher.get(url)
        assert outcome.text == "example.com\n"
        assert outcome.stale is True
        assert outcome.error
        assert fetcher.stats.stale_hits == 1


def test_no_snapshot_and_no_network_raises(tmp_path: Path, server: str) -> None:
    STATUS["/missing.txt"] = 404
    with Fetcher(tmp_path, retries=0) as fetcher:
        with pytest.raises(FetchError):
            fetcher.get(f"{server}/missing.txt")


def test_offline_uses_snapshot_only(tmp_path: Path, server: str) -> None:
    url = f"{server}/list.txt"
    RESPONSES["/list.txt"] = b"a.com\n"
    with Fetcher(tmp_path) as fetcher:
        fetcher.get(url)

    with Fetcher(tmp_path, offline=True) as fetcher:
        assert fetcher.get(url).text == "a.com\n"

    with Fetcher(tmp_path, offline=True) as fetcher:
        with pytest.raises(FetchError):
            fetcher.get(f"{server}/other.txt")


def test_binary_payload_is_preserved(tmp_path: Path, server: str) -> None:
    raw = bytes(range(256))
    RESPONSES["/blob"] = raw
    with Fetcher(tmp_path) as fetcher:
        assert fetcher.get(f"{server}/blob").content == raw

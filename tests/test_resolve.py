from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from builder.config import Paths
from builder.fetch import Fetcher
from builder.resolve import Resolver
from builder.spec import CategorySpec, Include, Upstream, Upstreams

FILES: dict[str, str] = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = FILES.get(self.path)
        if body is None:
            self.send_error(404)
            return
        raw = body.encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

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
    FILES.clear()


def _spec(tmp_path, includes, add=()):
    from pathlib import Path

    from builder.model import Rule

    return CategorySpec(
        id="test",
        path=Path(tmp_path) / "test.yaml",
        description="test",
        meta={"description": "test"},
        includes=list(includes),
        add=[Rule.parse(r) for r in add],
    )


def _upstreams(base: str) -> Upstreams:
    upstream = Upstream(
        id="v2fly",
        title="v2fly",
        format="v2fly",
        url_template=base + "/{category}",
        url=None,
        ref="master",
        license="MIT",
        license_url="",
        homepage="",
    )
    return Upstreams({"v2fly": upstream}, timeout_seconds=5, retries=0, cache_ttl_hours=0)


def test_v2fly_include_is_recursive_and_attribute_filtered(tmp_path, server):
    FILES["/ai"] = "openai.com\nfull:chat.openai.com @cn\ninclude:base\n"
    FILES["/base"] = "example.net\n"
    upstreams = _upstreams(server)
    with Fetcher(tmp_path / "cache") as fetcher:
        resolver = Resolver(upstreams, fetcher)
        resolved = resolver.resolve(
            _spec(tmp_path, [Include("v2fly", ("ai",), ("cn",))], add=("DOMAIN-SUFFIX,manual.com",))
        )
    values = {str(rule) for rule in resolved.rules}
    assert "DOMAIN-SUFFIX,openai.com" in values
    assert "DOMAIN-SUFFIX,example.net" in values
    assert "DOMAIN,chat.openai.com" not in values  # excluded by @cn
    assert "DOMAIN-SUFFIX,manual.com" in values
    assert resolved.from_upstream == 2
    assert resolved.manual == 1


def test_missing_category_is_reported_not_fatal(tmp_path, server):
    FILES["/root"] = "a.com\n"
    upstreams = _upstreams(server)
    with Fetcher(tmp_path / "cache") as fetcher:
        resolver = Resolver(upstreams, fetcher)
        good = resolver.resolve(_spec(tmp_path, [Include("v2fly", ("root",))]))
        bad = resolver.resolve(_spec(tmp_path, [Include("v2fly", ("nope",))]))
    assert good.missing == []
    assert bad.missing == ["nope"]
    assert bad.rules == []


def test_removals_apply_by_value(tmp_path, server):
    FILES["/root"] = "keep.com\ndrop.com\n"
    upstreams = _upstreams(server)
    from pathlib import Path

    spec = _spec(tmp_path, [Include("v2fly", ("root",))])
    spec.removes = {"drop.com": "test reason"}
    with Fetcher(tmp_path / "cache") as fetcher:
        resolved = Resolver(upstreams, fetcher).resolve(spec)
    assert [rule.value for rule in resolved.rules] == ["keep.com"]
    assert Path(tmp_path).exists()

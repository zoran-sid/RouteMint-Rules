"""Resolve category definitions into flat rule lists.

Two upstream shapes are supported:

* ``v2fly-dat`` - one ``dlc.dat`` download holds all 1556 categories, so no
  recursive ``include:`` walking is needed (and no thousand-request build).
* everything else - one file per include, parsed with the declared format.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .fetch import Fetcher, FetchError
from .model import Rule
from .parse import PARSERS, ParsedDocument, parse_v2fly_dat
from .spec import CategorySpec, Include, Upstream, Upstreams


@dataclass
class ResolvedCategory:
    spec: CategorySpec
    rules: list[Rule] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    degraded: bool = False
    invalid: int = 0
    unsupported: int = 0
    from_upstream: int = 0
    manual: int = 0
    missing: list[str] = field(default_factory=list)


class ResolveError(Exception):
    pass


class Resolver:
    def __init__(self, upstreams: Upstreams, fetcher: Fetcher) -> None:
        self.upstreams = upstreams
        self.fetcher = fetcher
        self._docs: dict[tuple[str, str], ParsedDocument] = {}
        self._dat: dict[str, dict[str, ParsedDocument]] = {}
        self._dat_stale: dict[str, bool] = {}

    def resolve(self, spec: CategorySpec) -> ResolvedCategory:
        resolved = ResolvedCategory(spec=spec)
        rules: list[Rule] = []
        urls: set[str] = set()

        for include in spec.includes:
            upstream = self.upstreams.upstreams.get(include.upstream)
            if upstream is None:
                raise ResolveError(f"{spec.id}: unknown upstream {include.upstream!r}")
            if upstream.format == "v2fly-dat":
                rules.extend(self._from_dat(upstream, include, resolved))
                urls.add(upstream.url or "")
                continue
            for doc in self._documents(upstream, include):
                urls.add(doc[0])
                for parsed in doc[1].rules:
                    if include.exclude_attributes and parsed.attributes & set(
                        include.exclude_attributes
                    ):
                        continue
                    rules.append(parsed.rule)
                resolved.invalid += doc[1].invalid
                resolved.unsupported += len(doc[1].unsupported)

        resolved.from_upstream = len(rules)
        resolved.urls = sorted(u for u in urls if u)
        resolved.degraded = any(
            (self.fetcher._mem.get(url) is not None and self.fetcher._mem[url].stale)
            for url in resolved.urls
        )
        if not spec.compose:
            rules.extend(spec.add)
            resolved.manual = len(spec.add)
        resolved.rules = [r for r in rules if r.value not in spec.removes]
        return resolved

    # -- v2fly dlc.dat ---------------------------------------------------
    def _load_dat(self, upstream: Upstream) -> dict[str, ParsedDocument]:
        if upstream.id in self._dat:
            return self._dat[upstream.id]
        if upstream.url is None:
            raise ResolveError(f"{upstream.id}: v2fly-dat requires url")
        try:
            outcome = self.fetcher.get_text(upstream.url)
        except FetchError as exc:
            raise ResolveError(f"{upstream.id}: {exc}") from exc
        try:
            documents = parse_v2fly_dat(outcome.content)
        except ValueError as exc:
            raise ResolveError(f"{upstream.id}: cannot parse dlc.dat: {exc}") from exc
        self._dat[upstream.id] = documents
        self._dat_stale[upstream.id] = outcome.stale
        return documents

    def _from_dat(
        self, upstream: Upstream, include: Include, resolved: ResolvedCategory
    ) -> list[Rule]:
        documents = self._load_dat(upstream)
        if self._dat_stale.get(upstream.id):
            resolved.degraded = True
        out: list[Rule] = []
        for category in include.categories:
            doc = documents.get(category)
            if doc is None:
                resolved.missing.append(category)
                continue
            resolved.invalid += doc.invalid
            resolved.unsupported += len(doc.unsupported)
            excluded = set(include.exclude_attributes)
            out.extend(
                parsed.rule
                for parsed in doc.rules
                if not excluded or not (parsed.attributes & excluded)
            )
        return out

    # -- single-file upstreams -------------------------------------------
    def _documents(self, upstream: Upstream, include: Include) -> list[tuple[str, ParsedDocument]]:
        categories = include.categories or ("",)
        out: list[tuple[str, ParsedDocument]] = []
        for category in categories:
            url = upstream.url_for(category if category else None)
            key = (upstream.id, category)
            if key not in self._docs:
                try:
                    outcome = self.fetcher.get_text(url)
                except FetchError as exc:
                    raise ResolveError(f"{upstream.id}/{category}: {exc}") from exc
                parser = PARSERS[upstream.format]
                if upstream.format == "apnic":
                    doc = parser(outcome.text, country=str(upstream.options.get("country", "CN")))
                else:
                    doc = parser(outcome.text)
                self._docs[key] = doc
            out.append((url, self._docs[key]))
        return out

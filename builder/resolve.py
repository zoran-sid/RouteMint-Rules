"""Resolve category definitions into flat rule lists.

Two upstream shapes are supported:

* ``v2fly-dat`` - one ``dlc.dat`` download holds all 1556 categories, so no
  recursive ``include:`` walking is needed (and no thousand-request build).
* text lists - one file per include, with ``include:`` expanded recursively
  under a depth limit and cycle guard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .fetch import Fetcher, FetchError
from .model import Rule
from .parse import PARSERS, ParsedDocument, parse_v2fly_dat
from .spec import CategorySpec, Include, Upstream, Upstreams

MAX_INCLUDE_DEPTH = 6


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
                if upstream.url:
                    urls.add(upstream.url)
                continue
            expand = self._expand_text(
                upstream, include, depth=0, seen=set(), resolved=resolved, urls=urls
            )
            rules.extend(expand)

        resolved.from_upstream = len(rules)
        resolved.urls = sorted(urls)
        resolved.degraded = resolved.degraded or any(
            (outcome := self.fetcher._mem.get(url)) is not None and outcome.stale
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
            outcome = self.fetcher.get(upstream.url)
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
        excluded = set(include.exclude_attributes)
        for category in include.categories:
            doc = documents.get(category)
            if doc is None:
                resolved.missing.append(category)
                continue
            resolved.invalid += doc.invalid
            resolved.unsupported += len(doc.unsupported)
            out.extend(
                parsed.rule
                for parsed in doc.rules
                if not excluded or not (parsed.attributes & excluded)
            )
        return out

    # -- text upstreams --------------------------------------------------
    def _document(self, upstream: Upstream, category: str) -> ParsedDocument:
        url = upstream.url_for(category or None)
        key = (upstream.id, category)
        if key in self._docs:
            return self._docs[key]
        try:
            outcome = self.fetcher.get(url)
        except FetchError as exc:
            if exc.status == 404:
                raise _Missing(category) from exc
            raise ResolveError(f"{upstream.id}/{category}: {exc}") from exc
        parser = PARSERS[upstream.format]
        if upstream.format == "apnic":
            doc = parser(outcome.text, country=str(upstream.options.get("country", "CN")))
        else:
            doc = parser(outcome.text)
        self._docs[key] = doc
        return doc

    def _expand_text(
        self,
        upstream: Upstream,
        include: Include,
        *,
        depth: int,
        seen: set[str],
        resolved: ResolvedCategory,
        urls: set[str],
    ) -> list[Rule]:
        if depth > MAX_INCLUDE_DEPTH:
            raise ResolveError(f"{upstream.id}: include depth exceeded")
        excluded = set(include.exclude_attributes)
        out: list[Rule] = []
        for category in include.categories or ("",):
            if category in seen:
                continue
            seen.add(category)
            try:
                doc = self._document(upstream, category)
            except _Missing:
                resolved.missing.append(category or upstream.url or upstream.id)
                continue
            urls.add(upstream.url_for(category or None))
            resolved.invalid += doc.invalid
            resolved.unsupported += len(doc.unsupported)
            out.extend(
                parsed.rule
                for parsed in doc.rules
                if not excluded or not (parsed.attributes & excluded)
            )
            if not upstream.url_template:
                continue
            for child in doc.includes:
                out.extend(
                    self._expand_text(
                        upstream,
                        Include(
                            upstream=include.upstream,
                            categories=(child,),
                            exclude_attributes=include.exclude_attributes,
                        ),
                        depth=depth + 1,
                        seen=seen,
                        resolved=resolved,
                        urls=urls,
                    )
                )
        return out


class _Missing(Exception):
    """A declared upstream category does not exist (usually an upstream rename)."""

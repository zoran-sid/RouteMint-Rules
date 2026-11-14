"""Command line entry point: ``python -m builder build``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import BuildError, build, clean_dist, load_previous_manifest
from .config import ConfigError, Paths
from .emit import EmitError, require_binary
from .report import summary_line


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="builder", description="RouteMint-Rules builder")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    sub = parser.add_subparsers(dest="command", required=True)

    build_cmd = sub.add_parser("build", help="build dist/ from sources/")
    build_cmd.add_argument("--refresh", action="store_true", help="ignore the fetch cache")
    build_cmd.add_argument("--offline", action="store_true", help="use snapshots only")
    build_cmd.add_argument("--mihomo-bin", help="path to the pinned mihomo binary")
    build_cmd.add_argument("--singbox-bin", help="path to the pinned sing-box binary")
    build_cmd.add_argument(
        "--validate", action="store_true", help="run mihomo -t on every rendered config"
    )
    build_cmd.add_argument("--previous-manifest", help="manifest.json of the previous release")
    build_cmd.add_argument("--previous-dist", help="previous dist/ tree, for changelog diffs")
    build_cmd.add_argument("--allow-drop", action="store_true", help="bypass the drop guard")
    build_cmd.add_argument(
        "--keep-dist", action="store_true", help="do not remove stale files before building"
    )
    build_cmd.add_argument(
        "--check-domains",
        action="store_true",
        help="resolve a sample of hand-added domains and report NXDOMAIN (report only)",
    )
    build_cmd.add_argument("--domain-sample", type=int, default=40)
    build_cmd.add_argument("--quiet", action="store_true")

    sub.add_parser("check", help="validate YAML configuration without touching the network")

    publish_cmd = sub.add_parser("publish", help="compute release notes and changed files")
    publish_cmd.add_argument("--dist", default="dist")
    publish_cmd.add_argument("--previous", help="manifest.json from the release branch")
    publish_cmd.add_argument("--tag", required=True)
    publish_cmd.add_argument("--notes-out", required=True)
    publish_cmd.add_argument("--changed-out", required=True)
    publish_cmd.add_argument("--changelog", default="CHANGELOG.md")

    qr_cmd = sub.add_parser("qr", help="regenerate docs/qr/*.png import codes")
    qr_cmd.add_argument("--out", default="docs/qr")

    purge_cmd = sub.add_parser("purge", help="purge changed files from the jsDelivr cache")
    purge_cmd.add_argument("--changed", required=True)
    purge_cmd.add_argument("--root", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    paths = Paths(Path(args.root).resolve())

    try:
        if args.command == "publish":
            from .publish import main as publish_main

            return publish_main(
                Path(args.dist),
                Path(args.previous) if args.previous else None,
                args.tag,
                Path(args.notes_out),
                Path(args.changed_out),
                Path(args.changelog) if args.changelog else None,
            )
        if args.command == "qr":
            from .qr import generate

            written = generate(paths, Path(args.out))
            print(f"wrote {len(written)} QR codes to {args.out}")
            return 0
        if args.command == "purge":
            from .publish import purge_from_changed

            return purge_from_changed(Path(args.changed), Path(args.root).resolve())

        if args.command == "check":
            from .spec import load_budgets, load_categories, load_presets, load_upstreams

            categories = load_categories(paths)
            presets = load_presets(paths, categories)
            load_upstreams(paths)
            load_budgets(paths)
            print(f"ok: {len(categories)} categories, {len(presets)} presets")
            return 0

        if not args.keep_dist:
            clean_dist(paths)
        mihomo_bin = None
        if args.mihomo_bin:
            mihomo_bin = require_binary("mihomo", args.mihomo_bin)
        singbox_bin = None
        if args.singbox_bin:
            singbox_bin = require_binary("sing-box", args.singbox_bin)

        result = build(
            paths,
            refresh=args.refresh,
            offline=args.offline,
            mihomo_bin=mihomo_bin,
            singbox_bin=singbox_bin,
            validate=args.validate,
            previous_manifest=Path(args.previous_manifest) if args.previous_manifest else None,
            previous_dist=Path(args.previous_dist) if args.previous_dist else None,
            allow_drop=args.allow_drop,
            check_domains=args.check_domains,
            domain_sample=args.domain_sample,
        )
    except (ConfigError, BuildError, EmitError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for violation in result.violations:
        print(f"violation: {violation}", file=sys.stderr)
    if not args.quiet:
        print(summary_line(result))
        print(f"dist: {result.dist}")
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

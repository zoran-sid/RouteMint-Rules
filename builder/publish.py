"""Release publishing helpers: change detection, release notes, jsDelivr purge.

The workflow owns git; this module only answers three questions:
did the routing content change, what should the release notes say, and which
jsDelivr paths need a purge.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

PURGE_URL = "https://purge.jsdelivr.net"
MAX_PURGE = 200


def content_paths(path: str) -> bool:
    return path.startswith(("rules/", "configs/", "routers/"))


def diff_files(current: dict, previous: dict | None) -> list[str]:
    old = (previous or {}).get("files", {})
    changed = [
        path
        for path, info in current.get("files", {}).items()
        if old.get(path, {}).get("sha256") != info.get("sha256")
    ]
    removed = [path for path in old if path not in current.get("files", {})]
    return sorted(changed + removed)


def changed_paths(manifest: dict, previous: dict | None) -> dict:
    changed = diff_files(manifest, previous)
    return {
        "changed": changed,
        "content_changed": any(content_paths(path) for path in changed),
        "count": len(changed),
    }


def release_notes(
    manifest: dict, changelog: Path | None, tag: str, changed: list[str]
) -> str:
    categories = manifest.get("categories", {})
    total = sum(info.get("total", 0) for info in categories.values())
    lines = [
        f"# {tag}",
        "",
        f"规则总数 **{total}**，分类 **{len(categories)}**，本次变更文件 **{len(changed)}**。",
        "",
        "## 预设规模",
        "",
        "| 预设 | ads-off | ads-light | ads-strict |",
        "|---|---|---|---|",
    ]
    for preset, info in sorted(manifest.get("presets", {}).items()):
        rules = info.get("rules", {})
        lines.append(
            f"| `{preset}` | {rules.get('ads-off', '-')} | "
            f"{rules.get('ads-light', '-')} | {rules.get('ads-strict', '-')} |"
        )
    if changed:
        lines += ["", "## 变更文件", "", "```"]
        lines += changed[:40]
        if len(changed) > 40:
            lines.append(f"... 其余 {len(changed) - 40} 个")
        lines += ["```"]
    if changelog and changelog.is_file():
        text = changelog.read_text(encoding="utf-8")
        day = manifest.get("generated_at", "")[:10]
        marker = f"## {day}"
        if marker in text:
            section = text.split(marker, 1)[1]
            section = section.split("\n## ", 1)[0]
            lines += ["", "## 当日规则变化", "", section.strip()]
    lines += [
        "",
        "订阅地址：`https://cdn.jsdelivr.net/gh/zoran-sid/RouteMint-Rules@release/`",
        "（分支缓存最长 12 小时；紧急更新请用 Raw 地址）",
    ]
    return "\n".join(lines) + "\n"


def purge_files(paths: list[str], *, owner: str, repo: str, branch: str) -> dict:
    """Best-effort jsDelivr purge; failures are logged, never raised."""
    results = {"purged": 0, "failed": []}
    if not paths:
        return results
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        for path in paths[:MAX_PURGE]:
            url = f"{PURGE_URL}/gh/{owner}/{repo}@{branch}/{path}"
            try:
                response = client.get(url)
                if response.status_code == 200:
                    results["purged"] += 1
                else:
                    results["failed"].append(f"{path}: HTTP {response.status_code}")
            except httpx.HTTPError as exc:  # pragma: no cover - network
                results["failed"].append(f"{path}: {exc}")
            time.sleep(0.2)
    return results


def main(
    dist: Path,
    previous: Path | None,
    tag: str,
    notes_out: Path,
    changed_out: Path,
    changelog: Path | None,
) -> int:
    manifest = json.loads((dist / "manifest.json").read_text(encoding="utf-8"))
    prev = None
    if previous and previous.is_file() and previous.stat().st_size:
        try:
            prev = json.loads(previous.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = None
    info = changed_paths(manifest, prev)
    notes_out.write_text(release_notes(manifest, changelog, tag, info["changed"]), encoding="utf-8")
    changed_out.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in info.items() if k != "changed"}, ensure_ascii=False))
    return 0


def purge_from_changed(changed: Path, root: Path) -> int:
    import yaml

    info = json.loads(changed.read_text(encoding="utf-8"))
    config = yaml.safe_load((root / "repo.yaml").read_text(encoding="utf-8"))
    github = config["github"]
    result = purge_files(
        info.get("changed", []),
        owner=github["owner"],
        repo=github["repo"],
        branch=github.get("release_branch", "release"),
    )
    print(f"purged {result['purged']} files, {len(result['failed'])} failures")
    for failure in result["failed"][:5]:
        print(f"  purge failed: {failure}")
    return 0

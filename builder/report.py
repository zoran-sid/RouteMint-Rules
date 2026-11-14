"""Build report, manifest and changelog.

The report is for humans (what changed, what was dropped and why); the manifest
is for machines (budgets, drop guard, changelog diffing).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .model import Rule, RuleType
from .spec import categories_for
from .optimize import OptimizationStats

CATEGORY_TITLES = {
    "private": "局域网与保留地址",
    "reject-ads": "广告",
    "reject-tracker": "追踪器",
    "reject-malware": "恶意域名",
}


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _counts_row(cid: str, item, budgets) -> list[str]:
    limit = budgets.category_limit(cid)
    used = item.counts["total"]
    pct = f"{used / limit:.0%}" if limit else "-"
    return [
        cid,
        str(item.counts["domain"]),
        str(item.counts["ip"]),
        str(item.counts["keyword"]),
        str(used),
        f"{limit} ({pct})",
    ]


def write_report(
    path: Path,
    *,
    builds: dict,
    presets,
    budgets,
    fetcher_stats: dict,
    conflicts: OptimizationStats,
    violations: list[str],
    warnings: list[str],
    previous: dict | None,
    config_checks: list[dict],
    generated_at: str,
) -> None:
    rows = [_counts_row(cid, item, budgets) for cid, item in sorted(builds.items())]
    total = sum(item.counts["total"] for item in builds.values())

    parts = [
        "# 构建报告",
        "",
        f"生成时间：`{generated_at}`　规则总数：**{total}**　分类：**{len(builds)}**",
        "",
        "## 分类规模",
        "",
        _table(["分类", "域名", "IP", "关键字", "合计", "预算"], rows),
        "",
        "## 预设规模",
        "",
        _table(
            ["预设", "ads-off", "ads-light", "ads-strict", "预算"],
            [
                [p.id]
                + [
                    str(sum(builds[c].counts["total"] for c in categories_for(p, tier)))
                    for tier in ("ads-off", "ads-light", "ads-strict")
                ]
                + [str(budgets.preset_limit(p.id))]
                for p in presets
            ],
        ),
        "",
        "## 冲突裁决",
        "",
    ]

    if conflicts.decisions:
        sample = conflicts.decisions[:40]
        parts.append(
            _table(
                ["被丢弃分类", "获胜分类", "规则", "原因"],
                [[d.category, d.winner, str(d.rule), d.reason] for d in sample],
            )
        )
        if conflicts.conflicts > len(sample):
            parts.append(f"\n（仅显示前 {len(sample)} 条，共 {conflicts.conflicts} 条。）")
    else:
        parts.append("无跨分类冲突。")

    if fetcher_stats:
        parts += [
            "",
            "## 上游抓取",
            "",
            _table(
                ["网络下载", "命中缓存", "沿用旧快照", "失败"],
                [
                    [
                        str(fetcher_stats.get("network", 0)),
                        str(fetcher_stats.get("cache_hits", 0)),
                        str(fetcher_stats.get("stale_hits", 0)),
                        str(len(fetcher_stats.get("failures", []))),
                    ]
                ],
            ),
        ]
        for failure in fetcher_stats.get("failures", [])[:10]:
            parts.append(f"- 失败：{failure}")

    parts += ["", "## 配置校验", ""]
    if config_checks:
        rows = [
            [c["file"], "PASS" if c["ok"] else "FAIL", c["output"][-300:].replace("\n", " ")]
            for c in config_checks
        ]
        parts.append(_table(["文件", "结果", "输出"], rows))
    else:
        parts.append("本次未运行 mihomo -t（未提供二进制）。")

    parts += ["", "## 警告", ""]
    parts += [f"- {w}" for w in warnings] or ["- 无"]

    parts += ["", "## 阻断项", ""]
    parts += [f"- {v}" for v in violations] or ["- 无"]

    if previous:
        parts += ["", "## 与上一版对比", ""]
        rows = []
        for cid, item in sorted(builds.items()):
            before = (previous.get("categories", {}).get(cid) or {}).get("total", 0)
            after = item.counts["total"]
            if before != after:
                delta = after - before
                rows.append([cid, str(before), str(after), f"{delta:+d}"])
        parts.append(_table(["分类", "上一版", "本版", "变化"], rows) if rows else "无变化。")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _read_list_values(path: Path) -> set[str]:
    values: set[str] = set()
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "," not in line:
            continue
        values.add(line)
    return values


def _ordered(rules: list[Rule]) -> list[str]:
    return [str(r) for r in sorted(set(rules))]


def write_changelog(
    path: Path,
    *,
    builds: dict,
    previous: dict | None,
    previous_dist: Path | None,
    generated_at: str,
    presets,
) -> None:
    day = generated_at[:10]
    header = "# 变更日志\n\n由每日构建自动生成。只记录规则层面的变化，格式变化不计。\n"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    if existing.startswith(header):
        existing = existing[len(header) :]
    marker = f"## {day}"
    existing = existing.split(marker)[0].strip()

    lines = [marker, "", f"构建时间：`{generated_at}`", ""]
    if not previous:
        lines.append("首次构建，无历史对比。")
    else:
        changed = 0
        for cid, item in sorted(builds.items()):
            before = (previous.get("categories", {}).get(cid) or {}).get("total", 0)
            after = item.counts["total"]
            if before != after:
                changed += 1
                lines.append(f"- **{cid}**：{before} → {after}（{after - before:+d}）")
                added: set[str] = set()
                removed: set[str] = set()
                if previous_dist:
                    old = _read_list_values(previous_dist / "rules" / cid / f"{cid}.list")
                    new = set(_ordered(item.rules))
                    added, removed = new - old, old - new
                if added:
                    lines.append(f"  - 新增：{', '.join(sorted(added)[:8])}"
                                 + (" …" if len(added) > 8 else ""))
                if removed:
                    lines.append(f"  - 删除：{', '.join(sorted(removed)[:8])}"
                                 + (" …" if len(removed) > 8 else ""))
        if not changed:
            lines.append("无规则变化。")
        lines.append("")
        lines.append(_preset_lines(builds, presets))

    body = "\n".join(lines).strip()
    path.write_text(
        header + "\n" + body + ("\n\n" + existing if existing else "") + "\n", encoding="utf-8"
    )


def _preset_lines(builds: dict, presets) -> str:
    rows = [
        f"| {preset.id} | "
        + " | ".join(
            str(sum(builds[c].counts["total"] for c in categories_for(preset, tier)))
            for tier in ("ads-off", "ads-light", "ads-strict")
        )
        + " |"
        for preset in presets
    ]
    return "\n".join(
        ["| 预设 | ads-off | ads-light | ads-strict |", "|---|---|---|---|", *rows]
    )


def summary_line(result) -> str:
    total = sum(item.counts["total"] for item in result.categories.values())
    return (
        f"{len(result.categories)} categories, {total} rules, "
        f"{len(result.presets)} presets, {len(result.violations)} violations"
    )


CATEGORY_BEGIN = "<!-- BEGIN CATEGORY TABLE -->"
CATEGORY_END = "<!-- END CATEGORY TABLE -->"


def update_readme_table(path: Path, builds: dict) -> bool:
    """Rewrite the category table between HTML markers in README.md.

    Keeping counts in the README means they can never drift from the build.
    """
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if CATEGORY_BEGIN not in text or CATEGORY_END not in text:
        return False
    rows = []
    for cid, item in sorted(builds.items()):
        strategy = str(item.spec.meta.get("strategy", "-"))
        rows.append([f"`{cid}`", item.spec.description, str(item.counts["total"]), strategy])
    table = _table(["分类", "内容", "条数", "推荐策略"], rows)
    before, rest = text.split(CATEGORY_BEGIN, 1)
    _, after = rest.split(CATEGORY_END, 1)
    path.write_text(f"{before}{CATEGORY_BEGIN}\n{table}\n{CATEGORY_END}{after}", encoding="utf-8")
    return True


def write_notices(path: Path, upstreams: dict, repo_url: str) -> None:
    rows = [
        [f"`{u.id}`", u.title, u.license, f"[{u.homepage}]({u.homepage})" if u.homepage else "-"]
        for u in upstreams.values()
    ]
    parts = [
        "# 第三方数据来源与许可证",
        "",
        "本仓库的代码、脚本与 `sources/` 下自维护的规则采用 MIT 许可证。",
        "构建产物另外包含下列上游的数据（或其派生集合），其版权归原作者所有，",
        "分发时请同时遵守对应许可证。",
        "",
        _table(["上游 ID", "项目", "许可证", "主页"], rows),
        "",
        "## 逐项说明",
        "",
    ]
    for upstream in upstreams.values():
        parts.append(f"### {upstream.title}")
        parts.append("")
        parts.append(f"- 许可证：{upstream.license}")
        if upstream.license_url:
            parts.append(f"- 许可证原文：{upstream.license_url}")
        if upstream.homepage:
            parts.append(f"- 项目主页：{upstream.homepage}")
        if upstream.notice:
            parts.append(f"- 备注：{upstream.notice}")
        parts.append("")
    parts += [
        "## 为什么没有 AdGuard DNS filter / EasyList",
        "",
        "AdGuard SDNS Filter 与 EasyList 分别是 GPL-3.0 与 GPL-3.0-or-later / CC-BY-SA-3.0。",
        "把它们的数据随 MIT 产物一起分发会产生许可证冲突，因此本仓库改用许可证兼容的来源：",
        "ShadowWhisperer/BlockLists（Unlicense）与 urlhaus-filter（CC0 数据部分）。",
        "如果你在本地构建时想自行接入 GPL 上游，请自行评估合规性，本仓库不代为分发。",
        "",
        f"仓库地址：{repo_url}",
    ]
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")

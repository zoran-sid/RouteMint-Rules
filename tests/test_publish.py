from __future__ import annotations

from pathlib import Path

from builder.publish import changed_paths, diff_files, release_notes


def manifest(files: dict[str, str]) -> dict:
    return {
        "generated_at": "2026-11-14T03:00:00+00:00",
        "categories": {"cn": {"total": 10}},
        "presets": {"cn-mainland": {"rules": {"ads-off": 1, "ads-light": 2, "ads-strict": 3}}},
        "files": {path: {"sha256": sha, "bytes": 1} for path, sha in files.items()},
    }


def test_diff_detects_added_changed_and_removed():
    current = manifest({"rules/a/a.list": "1", "configs/x/mihomo.yaml": "2"})
    previous = manifest({"rules/a/a.list": "1", "rules/b/b.list": "3"})
    assert diff_files(current, previous) == ["configs/x/mihomo.yaml", "rules/b/b.list"]


def test_content_change_only_counts_rules_and_configs():
    current = manifest({"rules/a/a.list": "2", "manifest.json": "x"})
    previous = manifest({"rules/a/a.list": "1", "manifest.json": "y"})
    info = changed_paths(current, previous)
    assert info["content_changed"] is True

    current = manifest({"build-report.md": "2"})
    previous = manifest({"build-report.md": "1"})
    assert changed_paths(current, previous)["content_changed"] is False


def test_first_run_is_a_content_change():
    info = changed_paths(manifest({"rules/a/a.list": "1"}), None)
    assert info["content_changed"] is True
    assert info["count"] == 1


def test_release_notes_include_preset_table_and_changelog(tmp_path: Path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# 变更日志\n\n## 2026-11-14\n\n- **cn**：10 → 12（+2）\n\n## 2026-11-13\n\n- old\n",
        encoding="utf-8",
    )
    notes = release_notes(manifest({"rules/a/a.list": "1"}), changelog, "build-2026", ["rules/a/a.list"])
    assert "| `cn-mainland` | 1 | 2 | 3 |" in notes
    assert "**cn**：10 → 12" in notes
    assert "2026-11-13" not in notes
    assert "rules/a/a.list" in notes

"""Filesystem layout and YAML loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigError(Exception):
    """A configuration file is missing, malformed or inconsistent."""


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def upstreams(self) -> Path:
        return self.root / "upstreams.yaml"

    @property
    def budgets(self) -> Path:
        return self.root / "budgets.yaml"

    @property
    def sources(self) -> Path:
        return self.root / "sources"

    @property
    def presets(self) -> Path:
        return self.root / "presets"

    @property
    def templates(self) -> Path:
        return self.root / "templates"

    @property
    def dist(self) -> Path:
        return self.root / "dist"

    @property
    def cache(self) -> Path:
        return self.root / ".cache" / "upstreams"

    @property
    def tests(self) -> Path:
        return self.root / "tests"


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise ConfigError(f"missing file: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    return data


def dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100)

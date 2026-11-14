from __future__ import annotations

import os
from pathlib import Path

import pytest

from builder.build import BuildResult, build
from builder.config import Paths

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def paths() -> Paths:
    return Paths(ROOT)


@pytest.fixture(scope="session")
def mihomo_bin() -> Path | None:
    explicit = os.environ.get("ROUTEMINT_MIHOMO_BIN")
    if explicit and Path(explicit).is_file():
        return Path(explicit).resolve()
    local = ROOT / ".cache" / "bin" / "mihomo"
    return local.resolve() if local.is_file() else None


@pytest.fixture(scope="session")
def built(paths: Paths, mihomo_bin: Path | None) -> BuildResult:
    """Build once per test session; the fetch cache makes this cheap."""
    return build(
        paths,
        offline=bool(os.environ.get("ROUTEMINT_OFFLINE")),
        mihomo_bin=mihomo_bin,
    )


@pytest.fixture(scope="session")
def preset_map(built: BuildResult) -> dict:
    return {preset.id: preset for preset in built.presets}

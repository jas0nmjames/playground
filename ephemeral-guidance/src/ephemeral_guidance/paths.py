from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path

    @property
    def assets_dir(self) -> Path:
        return self.project_root / "assets_generative"

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def duckdb_path(self) -> Path:
        return self.data_dir / "warehouse.duckdb"

    @property
    def insights_json_path(self) -> Path:
        return self.data_dir / "insights.json"

    @property
    def evidence_dir(self) -> Path:
        return self.data_dir / "evidence"


def default_paths() -> ProjectPaths:
    # This package lives at: ephemeral-guidance/src/ephemeral_guidance
    # Project root is:     ephemeral-guidance/
    project_root = Path(__file__).resolve().parents[2]
    return ProjectPaths(project_root=project_root)

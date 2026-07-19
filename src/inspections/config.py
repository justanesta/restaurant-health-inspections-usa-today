"""Load and type the source registry (config/sources.yaml).

The registry is the ONE place sources are declared. The pipeline iterates
`load_config().enabled_sources()`; nothing else hard-codes the source list.
"""

from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from .models import ExtractionMethod
from .paths import SOURCES_CONFIG


class GeoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: str = "county"
    county_field: str | None = None      # NY: resolve FIPS from this per-row county name
    county_fips: str | None = None       # LA/ABQ: whole source is one county
    state_fips: str | None = None
    state: str | None = None


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    name: str
    enabled: bool = True
    extraction_method: ExtractionMethod
    publisher: str | None = None
    landing_url: str | None = None
    grain: str | None = None
    geo: GeoConfig
    # Method-specific blocks kept as plain dicts — each extractor knows its own shape.
    soda: dict[str, Any] | None = None
    arcgis: dict[str, Any] | None = None
    pdf: dict[str, Any] | None = None

    @property
    def dataset_id(self) -> str | None:
        for block in (self.soda, self.arcgis, self.pdf):
            if block and "dataset_id" in block:
                return block["dataset_id"]
        return None


class PipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    window_days: int = 90
    sample_limit: int | None = None
    sources: list[SourceConfig]

    def enabled_sources(self) -> list[SourceConfig]:
        return [s for s in self.sources if s.enabled]

    def get(self, key: str) -> SourceConfig:
        for s in self.sources:
            if s.key == key:
                return s
        raise KeyError(f"No source with key {key!r} in {SOURCES_CONFIG}")


def load_config(path=SOURCES_CONFIG) -> PipelineConfig:
    with open(path) as fh:
        return PipelineConfig.model_validate(yaml.safe_load(fh))

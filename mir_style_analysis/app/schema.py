"""Versioned, serialisable representation shared by every pipeline stage."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "1.0.0"
FEATURE_VERSION = "librosa-heuristic-1.0.0"

@dataclass
class TrackFeatures:
    # Values in numeric are documented in README and are finite floats or absent.
    duration_seconds: float
    bpm: float | None
    key: str | None
    mode: str | None
    genre: str | None
    genre_method: str
    genre_confidence: float | None
    mood: str | None
    mood_method: str
    instruments: dict[str, float] = field(default_factory=dict)
    numeric: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION
    feature_version: str = FEATURE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TrackFeatures":
        return cls(**value)

@dataclass
class CatalogueTrack:
    id: str
    title: str
    artist: str
    album: str | None
    provenance: str | None
    features: TrackFeatures

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["features"] = self.features.to_dict()
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CatalogueTrack":
        data = dict(value)
        data["features"] = TrackFeatures.from_dict(data["features"])
        return cls(**data)

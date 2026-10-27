from __future__ import annotations
import json
from pathlib import Path
from .schema import CatalogueTrack

class Catalogue:
    """Small JSON catalogue; replaceable persistence boundary for PostgreSQL later."""
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def all(self) -> list[CatalogueTrack]:
        if not self.path.exists(): return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [CatalogueTrack.from_dict(x) for x in payload.get("tracks", [])]

    def upsert(self, track: CatalogueTrack) -> None:
        items = {item.id: item for item in self.all()}
        items[track.id] = track
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"tracks": [x.to_dict() for x in items.values()]}, indent=2), encoding="utf-8")

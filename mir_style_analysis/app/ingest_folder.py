"""Batch-ingest a folder of rights-cleared reference audio.

Examples:
    python -m app.ingest_folder "D:\\Music\\references" --recursive
    python -m app.ingest_folder "D:\\Music\\references" --artist "Various Artists"

Filenames of the form ``Artist - Title.ext`` provide useful metadata. Files
without that pattern use the filename as the title and --artist-default (or
"Unknown artist") as the artist; those records remain searchable but cannot
provide strong artist-style evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .analysis import extract
from .catalogue import Catalogue
from .schema import CatalogueTrack

SUPPORTED = {".mp3", ".wav", ".flac"}


def metadata_from_filename(path: Path, default_artist: str) -> tuple[str, str]:
    stem = re.sub(r"[_]+", " ", path.stem).strip()
    if " - " in stem:
        artist, title = stem.split(" - ", 1)
        if artist.strip() and title.strip():
            return artist.strip(), title.strip()
    return default_artist, stem or path.name


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-ingest a folder into the MIR reference catalogue.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--catalogue", default="data/catalogue.json", help="Catalogue JSON path.")
    parser.add_argument("--recursive", action="store_true", help="Include nested folders.")
    parser.add_argument("--artist-default", default="Unknown artist", help="Artist used when the filename is not Artist - Title.")
    parser.add_argument("--album-default", default=None)
    parser.add_argument("--dry-run", action="store_true", help="List files without decoding or writing records.")
    args = parser.parse_args()

    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        parser.error(f"Folder does not exist: {folder}")
    files = sorted(folder.rglob("*") if args.recursive else folder.glob("*"))
    files = [path for path in files if path.is_file() and path.suffix.lower() in SUPPORTED]
    if args.dry_run:
        for path in files:
            artist, title = metadata_from_filename(path, args.artist_default)
            print(f"{path.name} -> {artist} / {title}")
        print(f"Dry run: {len(files)} supported file(s).")
        return

    catalogue = Catalogue(args.catalogue)
    existing = {track.id for track in catalogue.all()}
    completed, skipped, failed = [], [], []
    for number, path in enumerate(files, 1):
        try:
            # extract() is intentionally done before upsert so corrupt audio
            # never creates a catalogue record.
            import hashlib
            track_id = hashlib.sha256(path.read_bytes()).hexdigest()[:24]
            artist, title = metadata_from_filename(path, args.artist_default)
            if track_id in existing:
                skipped.append({"file": str(path), "reason": "duplicate content"})
                print(f"[{number}/{len(files)}] skipped duplicate: {path.name}")
                continue
            features = extract(path)
            catalogue.upsert(CatalogueTrack(track_id, title, artist, args.album_default, f"local folder: {folder}", features))
            existing.add(track_id)
            completed.append({"file": str(path), "track_id": track_id, "title": title, "artist": artist})
            print(f"[{number}/{len(files)}] ingested: {artist} - {title}")
        except Exception as exc:
            failed.append({"file": str(path), "error": str(exc)})
            print(f"[{number}/{len(files)}] failed: {path.name}: {exc}")

    summary = {"folder": str(folder), "found": len(files), "ingested": len(completed), "skipped": len(skipped), "failed": len(failed), "failures": failed}
    print(json.dumps(summary, indent=2))
    if failed:
        print("Some files failed; successful records were retained. Fix the listed files and run the command again.")


if __name__ == "__main__":
    main()

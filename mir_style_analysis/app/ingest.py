"""CLI: python -m app.ingest audio.wav --title Title --artist Artist --genre optional"""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path
from .analysis import extract
from .catalogue import Catalogue
from .schema import CatalogueTrack

def main():
    p=argparse.ArgumentParser(); p.add_argument("audio"); p.add_argument("--title",required=True); p.add_argument("--artist",required=True); p.add_argument("--album"); p.add_argument("--provenance",default="local ingestion"); p.add_argument("--catalogue",default="data/catalogue.json"); args=p.parse_args()
    audio=Path(args.audio); features=extract(audio)
    track_id=hashlib.sha256(audio.read_bytes()).hexdigest()[:24]
    Catalogue(args.catalogue).upsert(CatalogueTrack(track_id,args.title,args.artist,args.album,args.provenance,features))
    print(f"Ingested {args.title} ({track_id}); genre={features.genre}; schema={features.schema_version}")
if __name__ == "__main__": main()

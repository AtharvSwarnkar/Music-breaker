from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from .schema import CatalogueTrack, TrackFeatures

WEIGHTS = {"tempo": .18, "key": .08, "rhythm": .12, "harmony": .16, "timbre": .22, "spectral": .14, "dynamics": .10}
GROUPS = {"tempo": ["bpm"], "rhythm": ["percussive_ratio", "zero_crossing_rate"], "harmony": ["harmonic_ratio", "mfcc_1_mean"], "timbre": ["mfcc_2_mean", "mfcc_3_mean", "mfcc_4_mean", "spectral_centroid_hz"], "spectral": ["spectral_rolloff_hz", "spectral_bandwidth_hz", "spectral_flatness"], "dynamics": ["rms_db", "dynamic_range_db"]}
KEYS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

def _value(f: TrackFeatures, name: str) -> float | None: return f.bpm if name == "bpm" else f.numeric.get(name)
def _numeric_distance(query: TrackFeatures, ref: TrackFeatures, names: list[str], pool: list[CatalogueTrack]) -> float | None:
    values = []
    for name in names:
        q, r = _value(query,name), _value(ref,name)
        population = [_value(t.features,name) for t in pool]; population = [x for x in population if x is not None]
        if q is None or r is None or len(population) < 2: continue
        spread = max(max(population)-min(population), 1e-6)
        values.append(min(1., abs(q-r)/spread))
    return sum(values)/len(values) if values else None

def _key_distance(query: TrackFeatures, ref: TrackFeatures) -> float | None:
    if not query.key or not ref.key: return None
    distance = abs(KEYS.index(query.key)-KEYS.index(ref.key)); circle = min(distance,12-distance)/6
    return min(1., circle + (.18 if query.mode != ref.mode else 0))

def rank(query: TrackFeatures, tracks: list[CatalogueTrack], limit: int = 5, genre_filter: bool = True) -> tuple[list[dict], bool]:
    pool = tracks
    filtered = bool(genre_filter and query.genre and query.genre != "unknown")
    if filtered:
        same = [t for t in tracks if t.features.genre == query.genre]
        if same: pool = same
        else: filtered = False
    results = []
    for item in pool:
        distances = {group: _numeric_distance(query,item.features,names,pool) for group,names in GROUPS.items()}
        distances["key"] = _key_distance(query,item.features)
        usable = {k:v for k,v in distances.items() if v is not None}
        if not usable: continue
        weight_sum = sum(WEIGHTS[k] for k in usable)
        normalized = sum(WEIGHTS[k]*v for k,v in usable.items()) / weight_sum
        contributions = {k: round(WEIGHTS[k]*(1-v)/weight_sum,4) for k,v in usable.items()}
        results.append({"track_id":item.id,"title":item.title,"artist":item.artist,"album":item.album,"similarity_index":round(1-normalized,4),"feature_evidence":contributions})
    return sorted(results,key=lambda x:x["similarity_index"],reverse=True)[:limit], filtered

def infer_artist(matches: list[dict], minimum_tracks: int = 2) -> dict:
    per_artist: dict[str, list[float]] = defaultdict(list)
    for match in matches:
        if match.get("artist"): per_artist[match["artist"]].append(match["similarity_index"])
    candidates = []
    for artist, scores in per_artist.items():
        # Best score plus diminishing evidence from further retrieved tracks limits catalogue-size bias.
        evidence = max(scores) + .25 * sum(sorted(scores,reverse=True)[1:])
        candidates.append((evidence, artist, len(scores)))
    if not candidates: return {"status":"insufficient_evidence","artist":None,"evidence_strength":0,"reason":"No retrieved reference tracks have artist metadata."}
    evidence, artist, count = max(candidates)
    if count < minimum_tracks: return {"status":"insufficient_evidence","artist":None,"evidence_strength":round(evidence,4),"reason":f"Only {count} retrieved track(s) support the leading artist; {minimum_tracks} are required."}
    return {"status":"supported_style_similarity","artist":artist,"evidence_strength":round(evidence,4),"supporting_tracks":count,"disclaimer":"This indicates similarity to retrieved reference tracks, not authorship proof."}

def explain(query: TrackFeatures, matches: list[dict], artist: dict) -> list[str]:
    lines = [f"Measured tempo is {query.bpm:.1f} BPM." if query.bpm else "Tempo could not be estimated.", f"Estimated key is {query.key or 'unavailable'} {query.mode or ''}.".strip()]
    if matches:
        top = matches[0]; strongest = sorted(top["feature_evidence"],key=top["feature_evidence"].get,reverse=True)[:3]
        lines.append(f"Top reference: {top['title']} by {top['artist']} (similarity index {top['similarity_index']:.2f}); strongest weighted agreements: {', '.join(strongest)}.")
    else: lines.append("No reference tracks were available for comparison.")
    lines.append(artist.get("disclaimer") or artist.get("reason", "Artist inference was not available."))
    return lines

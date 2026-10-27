# Explainable Music Information Retrieval (isolated implementation)

This folder is independent of the existing `backend/` and `frontend/` code. It implements the requested upload-to-results pipeline:

`validate upload → decode/preprocess → feature extraction → versioned features → optional genre filter → weighted exact song ranking → artist evidence aggregation → explanations → website response`.

## Run

Use a working Python 3.10+ environment (the repository's checked-in `backend/venv` currently points at a deleted Python installation):

```powershell
cd D:\MusicAI\mir_style_analysis
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`; the API serves the bundled website from the same origin. If you instead host `web/` elsewhere, set `MIR_CORS_ORIGINS` to that origin and point `web/app.js` at the API origin.

## Add legitimate reference tracks

No fake catalogue records are created. Ingest tracks only when you hold the relevant rights and have accurate metadata:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m app.ingest path\to\reference.wav --title "Track" --artist "Artist" --album "Album"
```

This writes `data/catalogue.json`. The stable ID is derived from audio content; re-ingestion updates it. Set `MIR_CATALOGUE_PATH` for a different persistence location.

For a whole folder, use the batch command. It recursively supports MP3, WAV, and FLAC, skips duplicate audio content, and continues past files that fail decoding:

```powershell
python -m app.ingest_folder "D:\Music\references" --recursive
```

Use filenames such as `Artist - Title.mp3` for automatic metadata. For files without that naming convention, supply a fallback artist:

```powershell
python -m app.ingest_folder "D:\Music\references" --recursive --artist-default "Various Artists"
```

Preview metadata without changing the catalogue using `--dry-run`. The command prints a JSON summary with counts and individual failures.

## Feature schema and semantics

`TrackFeatures` is schema `1.0.0` / feature pipeline `librosa-heuristic-1.0.0`. It stores duration (s), BPM, key/mode, categorical labels, instrument spectral-evidence indices, and named numeric features: beat count, harmonic/percussive ratios, MFCC means, spectral centroid/rolloff/bandwidth/flatness, zero-crossing rate, RMS dB, and dynamic range dB. Missing values are `null`; no missing values are silently replaced for ranking.

Genre, mood, and instrument labels are deterministic documented heuristics—not trained or calibrated model predictions. Instrument values are spectral-evidence indices normalized to 100, not source-separated contribution percentages. Key is estimated from chroma/template correlation. These disclosures are returned in every API response.

Similarity uses per-group normalized distances and explicit weights in `app/retrieval.py`; it never concatenates unlike raw features. Key uses chromatic-circle distance. Genre filtering is optional and falls back to the full catalogue if it would return no candidates. `similarity_index` is an ordering score, not a probability. Artist style is inferred only from retrieved song metadata, with best-plus-diminishing evidence and a two-track minimum; otherwise it returns `insufficient_evidence`.

## API

- `GET /api/health` — service and catalogue count.
- `GET /api/catalogue` — catalogue count/schema.
- `POST /api/analyze?genre_filter=true` — multipart `file`, returns computed measurements, feature evidence, ranked tracks, artist result, limitations.

Uploads accept MP3/WAV/FLAC, reject empty/unsupported/over-100-MB files, and report decoding errors as 422. The process analyzes the first five minutes to bound resource use.

## Tests

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -q
```

The test suite covers schema persistence, weighted ranking and feature evidence, genre filtering, insufficient/supported artist inference, and the API's valid/empty/unsupported upload contract. Add fixture-audio integration tests after installing a working Python environment; do not use copyrighted uploads as test fixtures without permission.

## Production next steps

For production, use PostgreSQL/object storage instead of JSON/local files, add background jobs and authentication/rate limiting, pin and evaluate licensed pretrained tagging models for genre/mood/instruments, and validate retrieval with a labelled, rights-cleared catalogue. This project does not claim accuracy or performance metrics without that evaluation.

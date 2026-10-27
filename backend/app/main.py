
"""FastAPI application for music instrument analysis.

Pipeline:
1. Validate and save the uploaded audio.
2. Run Demucs source separation.
3. Locate the other.wav stem.
4. Explicitly load CLAP.
5. Run AnalysisService on the separated audio.
6. Validate and return the analysis.
7. Clean up temporary files.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import uuid
from pathlib import Path

import librosa
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import DEMUCS_MODEL, TEMP_DIR, UPLOADS_DIR
from app.feature_extraction.instrument.separator import DemucsSeparator
from app.models.clap_model import clap_model
from app.services.analysis_service import AnalysisService

# The shared MIR package remains independently runnable, while this import
# makes its feature schema/retrieval pipeline available to the legacy API.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mir_style_analysis.app.analysis import extract as extract_mir_features
from mir_style_analysis.app.catalogue import Catalogue
from mir_style_analysis.app.retrieval import explain as explain_mir, infer_artist, rank

logger = logging.getLogger(__name__)

app = FastAPI(title="MusicAI API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac"}
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024
MIR_CATALOGUE = Catalogue(
    os.getenv(
        "MIR_CATALOGUE_PATH",
        str(PROJECT_ROOT / "mir_style_analysis" / "data" / "catalogue.json"),
    )
)


@app.get("/")
def home():
    return {
        "status": "running",
        "project": "MusicAI",
        "version": app.version,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze_song(file: UploadFile = File(...)):
    filename = file.filename or "upload"
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        file.file.close()
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Upload MP3, WAV, or FLAC.",
        )

    song_id = uuid.uuid4().hex

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    uploaded_path = UPLOADS_DIR / f"{song_id}{extension}"
    stem_directory = TEMP_DIR / DEMUCS_MODEL / song_id

    try:
        # 1. Save and validate the upload.
        size = 0

        with uploaded_path.open("wb") as destination:
            while True:
                chunk = file.file.read(CHUNK_BYTES)

                if not chunk:
                    break

                size += len(chunk)

                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Audio upload exceeds the 100 MB limit.",
                    )

                destination.write(chunk)

        if size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        try:
            duration_seconds = float(
                librosa.get_duration(path=str(uploaded_path))
            )
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail="The uploaded file could not be decoded as audio.",
            ) from exc

        logger.info(
            "[1/5] Upload accepted: %s, %d bytes, %.2f seconds",
            filename,
            size,
            duration_seconds,
        )

        # 2. Run the MIR pipeline on the original upload. Unlike the old
        # source-separation path, this does not need CLAP/Demucs to succeed.
        features = extract_mir_features(uploaded_path)
        matches, genre_filter_applied = rank(features, MIR_CATALOGUE.all())
        artist = infer_artist(matches)
        mir_result = {
            "features": features.to_dict(),
            "similar_songs": matches,
            "genre_filter_applied": genre_filter_applied,
            "artist_style_inference": artist,
            "explanations": explain_mir(features, matches, artist),
            "limitations": [
                "Similarity index is a weighted distance score, not a calibrated probability.",
                "An empty catalogue produces no similarity or artist-style result.",
                *features.warnings,
            ],
        }
        result = {
            # The existing frontend can still use these summary fields.
            "analysis": [],
            "timelines": {},
            "song_level_scores": features.instruments,
            "contribution": features.instruments,
            "instrument_contribution": features.instruments,
            "presence": {},
            "window_coverage_percent": {},
            "score_semantics": (
                "Spectral-evidence indices normalized to 100; not source-separated "
                "instrument contribution percentages or calibrated probabilities."
            ),
            "mir": mir_result,
            "song": {
            "id": song_id,
            "filename": filename,
            "duration_seconds": round(duration_seconds, 3),
            },
        }

        # Preserve the old CLAP/Demucs analysis as an optional enhancement.
        # It cannot break all analysis when a model, GPU, or model download is unavailable.
        if os.getenv("MUSICAI_ENABLE_LEGACY_PIPELINE", "false").lower() == "true":
            try:
                separator = DemucsSeparator()
                separator.separate(str(uploaded_path))
                other_wav = stem_directory / "other.wav"
                if not other_wav.is_file():
                    raise RuntimeError(f"Demucs output not found: {other_wav}")
                clap_model.load()
                legacy_result = AnalysisService().analyze(str(other_wav))
                if not isinstance(legacy_result, dict):
                    raise RuntimeError("AnalysisService returned an unexpected response type.")
                result.update(legacy_result)
                result["legacy_instrument_status"] = {"status": "completed"}
            except Exception as legacy_exc:
                logger.exception("Optional legacy instrument pipeline failed")
                result["legacy_instrument_status"] = {
                    "status": "unavailable",
                    "detail": str(legacy_exc),
                }

        return result

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Music analysis pipeline failed")

        raise HTTPException(
            status_code=500,
            detail=(
                "Music analysis failed. Check the backend terminal "
                "for the stage and full traceback."
            ),
        ) from exc

    finally:
        file.file.close()
        uploaded_path.unlink(missing_ok=True)

        if stem_directory.exists():
            shutil.rmtree(stem_directory, ignore_errors=True)

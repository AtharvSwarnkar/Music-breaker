
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
import shutil
import uuid
from pathlib import Path

import librosa
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import DEMUCS_MODEL, TEMP_DIR, UPLOADS_DIR
from app.feature_extraction.instrument.separator import DemucsSeparator
from app.models.clap_model import clap_model
from app.services.analysis_service import AnalysisService

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

        # 2. Separate the audio using Demucs.
        logger.info("[2/5] Starting Demucs separation")

        separator = DemucsSeparator()
        separator.separate(str(uploaded_path))

        logger.info("[2/5] Demucs separation completed")

        # 3. Locate the expected separated stem.
        other_wav = stem_directory / "other.wav"

        if not other_wav.is_file():
            logger.error("Demucs output not found: %s", other_wav)

            raise RuntimeError(
                "Demucs completed, but other.wav was not found at: "
                f"{other_wav}"
            )

        logger.info("[3/5] Using separated stem: %s", other_wav)

        # 4. Explicitly load CLAP so loading errors are visible here.
        logger.info("[4/5] Loading CLAP model")

        try:
            clap_model.load()
        except Exception:
            logger.exception("CLAP model loading failed")
            raise

        logger.info("[4/5] CLAP model load call completed")

        # 5. Analyze the stem with the existing analysis pipeline.
        logger.info("[5/5] Starting AnalysisService")

        service = AnalysisService()
        result = service.analyze(str(other_wav))

        if not isinstance(result, dict):
            raise RuntimeError(
                "AnalysisService returned an unexpected response type."
            )

        required_keys = {
            "analysis",
            "timelines",
            "presence",
            "contribution",
        }

        missing_keys = required_keys.difference(result.keys())

        if missing_keys:
            raise RuntimeError(
                "AnalysisService response is missing keys: "
                + ", ".join(sorted(missing_keys))
            )

        analysis = result.get("analysis")

        if not isinstance(analysis, list) or not analysis:
            raise RuntimeError(
                "CLAP analysis returned no analysis windows. "
                "Check song_analyzer.py and detector.py."
            )

        logger.info(
            "Analysis completed successfully: %d windows",
            len(analysis),
        )
        logger.info("Response keys: %s", list(result.keys()))

        result["song"] = {
            "id": song_id,
            "filename": filename,
            "duration_seconds": round(duration_seconds, 3),
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

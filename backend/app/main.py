
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import DEMUCS_MODEL, TEMP_DIR, UPLOADS_DIR
from app.feature_extraction.instrument.separator import DemucsSeparator
from app.services.analysis_service import AnalysisService


app = FastAPI(
    title="MusicAI API",
    version="1.0.0",
)

# Allow the local React/Vite frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac"}


@app.get("/")
def home():
    return {
        "status": "running",
        "project": "MusicAI",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze_song(file: UploadFile = File(...)):
    """
    Upload an audio file, separate its stems with Demucs,
    and analyze the resulting other.wav using the existing pipeline.
    """

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Upload MP3, WAV, or FLAC.",
        )

    song_id = uuid.uuid4().hex
    song_name = f"{song_id}{extension}"

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    uploaded_path = UPLOADS_DIR / song_name

    try:
        # Save the uploaded audio.
        with uploaded_path.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)

        # Run the existing Demucs source-separation pipeline.
        separator = DemucsSeparator()
        separator.separate(str(uploaded_path))

        # Demucs normally writes stems to:
        # TEMP_DIR / DEMUCS_MODEL / uploaded_filename_without_extension
        stem_directory = (
            TEMP_DIR
            / DEMUCS_MODEL
            / uploaded_path.stem
        )

        other_wav = stem_directory / "other.wav"

        if not other_wav.exists():
            raise HTTPException(
                status_code=500,
                detail=(
                    "Demucs completed, but other.wav was not found. "
                    "Check the Demucs output directory and logs."
                ),
            )

        # Reuse your existing analysis service.
        service = AnalysisService()
        result = service.analyze(str(other_wav))

        return {
            "song": {
                "id": song_id,
                "filename": file.filename,
                "duration_seconds": len(result["analysis"]),
            },
            **result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        # Log the full exception in the backend terminal.
        print(f"Song analysis failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Song analysis failed: {str(exc)}",
        ) from exc

    finally:
        file.file.close()

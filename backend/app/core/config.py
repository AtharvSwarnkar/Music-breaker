from pathlib import Path

# app directory
BASE_DIR = Path(__file__).resolve().parents[1]

# Common folders
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"

# Models
DEMUCS_MODEL = "htdemucs"
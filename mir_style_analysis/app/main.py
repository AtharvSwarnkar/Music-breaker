from __future__ import annotations
import os, shutil, tempfile, uuid
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .analysis import extract
from .catalogue import Catalogue
from .retrieval import explain, infer_artist, rank

ROOT = Path(__file__).resolve().parents[1]
catalogue = Catalogue(os.getenv("MIR_CATALOGUE_PATH", str(ROOT / "data" / "catalogue.json")))
app = FastAPI(title="Explainable MIR", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("MIR_CORS_ORIGINS","http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"])
ALLOWED = {".mp3", ".wav", ".flac"}; MAX_BYTES = 100 * 1024 * 1024

@app.get("/api/health")
def health(): return {"status":"ok", "catalogue_tracks":len(catalogue.all())}
@app.get("/api/catalogue")
def catalogue_status(): return {"count":len(catalogue.all()), "schema":"1.0.0"}

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), genre_filter: bool = True):
    suffix = Path(file.filename or "upload").suffix.lower()
    if suffix not in ALLOWED: raise HTTPException(415,"Supported formats: MP3, WAV, FLAC.")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as output:
            temp_path = Path(output.name); total=0
            while part := await file.read(1024*1024):
                total += len(part)
                if total > MAX_BYTES: raise HTTPException(413,"Maximum upload size is 100 MB.")
                output.write(part)
        if not total: raise HTTPException(400,"The uploaded file is empty.")
        features = extract(temp_path)
        matches, did_filter = rank(features,catalogue.all(),genre_filter=genre_filter)
        artist = infer_artist(matches)
        return {"analysis_id":uuid.uuid4().hex,"filename":file.filename,"features":features.to_dict(),"similar_songs":matches,"genre_filter_applied":did_filter,"artist_style_inference":artist,"explanations":explain(features,matches,artist),"limitations":["Similarity index is a weighted distance score, not a calibrated probability.","An empty catalogue produces no similarity or artist-style result.",*features.warnings]}
    except HTTPException: raise
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    except Exception as exc: raise HTTPException(422,"Audio could not be decoded or analyzed.") from exc
    finally:
        await file.close()
        if temp_path: temp_path.unlink(missing_ok=True)

# Mounted last so API routes retain priority. The website is served from the same
# origin and can use its relative /api/analyze URL without CORS configuration.
app.mount("/", StaticFiles(directory=str(ROOT / "web"), html=True), name="web")

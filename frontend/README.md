# SONORA — Music Analysis UI

A responsive React/Vite frontend for the music analysis backend. It includes a liquid-glass interface, audio upload and playback, a waveform timeline, per-second instrument line charts, contribution summaries, frame inspection, and JSON export.

## Run locally

Requirements: Node.js 18+

```bash
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Connect to the FastAPI backend

Set `.env` to the backend origin and the actual analysis endpoint:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_ANALYZE_ENDPOINT=/api/analyze
```

The UI sends `POST {VITE_API_BASE_URL}{VITE_ANALYZE_ENDPOINT}` as `multipart/form-data` with the audio file under the field name `file`. If your backend uses a different upload field or route, edit `src/lib/api.js`.

**Important:** The supplied files were test scripts for Python services, not the FastAPI application/router. They show `SongAnalyzer.analyze(path)` returning window-based analysis, plus instrument percentages and stem analysis, but do not define an HTTP route or response schema. Therefore the route above is a configurable integration default, not a claim that your backend already exposes it. To make browser requests work, the backend needs a route accepting the upload and returning JSON. Enable CORS for `http://localhost:5173`.

Example FastAPI adapter (adjust imports and service response to your actual backend):

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil, tempfile

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    suffix = Path(file.filename or "track.wav").suffix or ".wav"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
        # Import and call the service already used by your project:
        # from app.services.song_analyzer import SongAnalyzer
        # windows = SongAnalyzer().analyze(temp_path)
        # return {"duration": ..., "windows": windows}
        raise HTTPException(501, "Replace this example body with your service call")
    finally:
        try: Path(temp_path).unlink(missing_ok=True)
        except (NameError, OSError): pass
```

Install `python-multipart` in the backend environment for FastAPI file uploads.

## Expected response shape

Best shape for second-level charts:

```json
{
  "duration": 214,
  "metadata": {"title": "Track name", "artist": "Optional"},
  "windows": [
    {"time": 0, "instruments": {"Drums": 0.8, "Bass": 0.4}},
    {"time": 1, "instruments": {"Drums": 0.6, "Bass": 0.5}}
  ],
  "instrument_percentages": {"Drums": 34, "Bass": 22}
}
```

`src/lib/audio.js` normalizes common alternatives (`analysis`, `results`, `frames`, score arrays and summary maps). Values above 1 are treated as percentages; values between 0 and 1 are treated as scores. Missing instrument values are treated as zero and instruments that are zero in every frame are omitted. If your model returns a different shape, update `normalizeAnalysis()` there.

## Verification checklist

- `npm run build` compiles the UI.
- Upload supports audio file selection and creates a local playback URL.
- Timeline click seeks in the uploaded audio; play/pause controls the native audio element.
- Per-second chart and frame inspector follow the current playhead.
- Analysis calls the configured backend route and reports HTTP/CORS/response errors in the UI.
- Export data downloads the raw backend JSON.
- Demo data is explicitly labeled as preview and is replaced after a successful backend analysis.

## Scope caveat

Only the Python test scripts and project specification were supplied in this conversation; the actual FastAPI app, route definitions, dependency file, and backend source were not. The frontend is prepared to connect through a configurable API contract, but the final route/field name must be matched to the actual backend before end-to-end connectivity can be verified.


## Dominant instrument graph

The instrument chart now selects the highest-scoring instrument independently for each one-second frame and displays that score only when it meets the adjustable benchmark (default 50%). Use the slider above the graph to change the benchmark. The frame inspector shows the winning instrument at the current playback position, or reports that no instrument clears the benchmark. This is based on the backend's returned scores; it should not be interpreted as calibrated acoustic loudness unless the backend model explicitly produces loudness measurements.

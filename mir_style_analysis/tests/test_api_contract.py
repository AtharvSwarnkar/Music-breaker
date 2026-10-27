from fastapi.testclient import TestClient
from app import main
from app.catalogue import Catalogue
from app.schema import CatalogueTrack, TrackFeatures

def feature():
    return TrackFeatures(2,120,"C","major","pop","test",.5,"neutral","test",{}, {"percussive_ratio":.4,"zero_crossing_rate":.1,"harmonic_ratio":.6,"mfcc_1_mean":1,"mfcc_2_mean":2,"mfcc_3_mean":3,"mfcc_4_mean":4,"spectral_centroid_hz":2000,"spectral_rolloff_hz":4000,"spectral_bandwidth_hz":1700,"spectral_flatness":.05,"rms_db":-18,"dynamic_range_db":8})

def test_upload_contract_and_empty_catalogue(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "catalogue", Catalogue(tmp_path / "catalogue.json"))
    monkeypatch.setattr(main, "extract", lambda _: feature())
    response = TestClient(main.app).post("/api/analyze", files={"file":("song.wav",b"not-real-audio","audio/wav")})
    assert response.status_code == 200
    assert response.json()["similar_songs"] == []
    assert response.json()["artist_style_inference"]["status"] == "insufficient_evidence"

def test_upload_rejects_unsupported_and_empty_files():
    client = TestClient(main.app)
    assert client.post("/api/analyze", files={"file":("song.txt",b"x","text/plain")}).status_code == 415
    assert client.post("/api/analyze", files={"file":("song.wav",b"","audio/wav")}).status_code == 400

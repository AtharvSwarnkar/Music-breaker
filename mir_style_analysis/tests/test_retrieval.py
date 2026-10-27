from app.retrieval import infer_artist, rank
from app.schema import CatalogueTrack, TrackFeatures

def feature(bpm=120, genre="pop", centroid=2000):
    return TrackFeatures(10,bpm,"C","major",genre,"test",.5,"neutral","test",{}, {"percussive_ratio":.4,"zero_crossing_rate":.1,"harmonic_ratio":.6,"mfcc_1_mean":1,"mfcc_2_mean":2,"mfcc_3_mean":3,"mfcc_4_mean":4,"spectral_centroid_hz":centroid,"spectral_rolloff_hz":4000,"spectral_bandwidth_hz":1700,"spectral_flatness":.05,"rms_db":-18,"dynamic_range_db":8})

def track(id, artist, bpm): return CatalogueTrack(id,id,artist,None,"test",feature(bpm))

def test_rank_prefers_close_tempo_and_reports_feature_evidence():
    results, filtered = rank(feature(),[track("near","A",121),track("far","B",180)])
    assert filtered and results[0]["track_id"] == "near"
    assert "tempo" in results[0]["feature_evidence"]

def test_empty_or_one_track_artist_is_insufficient_evidence():
    assert infer_artist([])["status"] == "insufficient_evidence"
    assert infer_artist([{"artist":"A","similarity_index":.9}])["status"] == "insufficient_evidence"

def test_artist_aggregation_uses_multiple_retrieved_tracks():
    result = infer_artist([{"artist":"A","similarity_index":.7},{"artist":"A","similarity_index":.6},{"artist":"B","similarity_index":.8}])
    assert result["artist"] == "A"

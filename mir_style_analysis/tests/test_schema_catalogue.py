from app.catalogue import Catalogue
from app.schema import CatalogueTrack, TrackFeatures

def test_catalogue_round_trip(tmp_path):
    f = TrackFeatures(1,100,"C","major","pop","test",.1,"neutral","test")
    store = Catalogue(tmp_path / "catalogue.json")
    store.upsert(CatalogueTrack("stable","A","Artist",None,"unit",f))
    assert store.all()[0].features.schema_version == "1.0.0"

from app.feature_extraction.instrument.separator import DemucsSeparator
from app.core.config import UPLOADS_DIR


separator = DemucsSeparator()

separator.separate(
    str(UPLOADS_DIR / "beliver.mp3")
)
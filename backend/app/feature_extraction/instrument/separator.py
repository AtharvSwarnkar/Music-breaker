import subprocess

from app.core.config import TEMP_DIR, DEMUCS_MODEL


class DemucsSeparator:
    def __init__(self):
        self.model = DEMUCS_MODEL

    def separate(self, audio_path: str):

        command = [
            "demucs",
            "-n",
            self.model,
            "-o",
            str(TEMP_DIR),
            audio_path
        ]

        print("Starting source separation...")

        subprocess.run(command, check=True)

        print("Source separation completed!")
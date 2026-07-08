import torch
import librosa
from app.models.clap_model import clap_model


class InstrumentDetector:

    def __init__(self):
        self.model = clap_model.model
        self.processor = clap_model.processor
        self.device = clap_model.device

    def detect(self, audio_path):

        audio, sr = librosa.load(audio_path, sr=48000, mono=True)

        prompts = [
            "An electric guitar is playing.",
            "An acoustic guitar is playing.",
            "A bass guitar is playing.",
            "A piano is playing.",
            "A drum kit is playing.",
            "A violin is playing.",
            "A flute is playing.",
            "A saxophone is playing."
        ]

        inputs = self.processor(
            text=prompts,
            audios=audio,
            sampling_rate=48000,
            return_tensors="pt",
            padding=True
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():

            outputs = self.model(**inputs)

            audio_embed = outputs.audio_embeds
            text_embed = outputs.text_embeds

            similarity = torch.matmul(
                audio_embed,
                text_embed.T
            )

        similarity = similarity.squeeze().cpu().numpy()

        results = list(zip(prompts, similarity))
        results.sort(key=lambda x: x[1], reverse=True)

        return results
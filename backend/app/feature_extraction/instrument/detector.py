
"""
Conservative multi-label instrument matching with CLAP.

CLAP cosine similarities are not probabilities. This module returns bounded
match scores after comparison with a generic-music baseline and a minimum
evidence threshold.

Thresholds should be calibrated on labelled audio before scores are described
as probabilities or physical instrument contributions.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

import numpy as np

from app.models.clap_model import clap_model


class InstrumentDetector:
    SAMPLE_RATE = 48_000

    # Keep prompts focused on instrument identity to reduce false positives.
    instrument_prompts = {
        "guitar": [
            "The sound of a guitar.",
            "A steel-string or electric guitar.",
            "A guitar playing musical notes.",
            "A distorted electric guitar with a driving rock tone.",
            "A warm acoustic guitar with a natural resonant tone.",
            "A clean, bright guitar tone with chiming overtones.",
            "A guitar strumming rhythmic chords.",
            "A guitar fingerpicking a melodic pattern.",
            "A guitar solo with bent notes and sustained vibrato.",
            "Guitar layered with bass and drums in a band mix.",
            "Guitar accompanying a lead vocalist.",
            "A guitar riff driving a rock or pop production.",
        ],
        "drums_percussion": [
            "The sound of a drum kit.",
            "A set of percussion instruments.",
            "Drums and percussion playing a rhythmic pattern.",
            "A punchy drum kit with a tight snare and deep kick.",
            "A warm, resonant hand percussion tone from congas and bongos.",
            "A bright drum kit with crisp cymbals and hi-hat.",
            "A drum kit groove with a steady kick and snare backbeat.",
            "Hand percussion played with open and muted strikes.",
            "A drum fill with rapid tom rolls into a cymbal crash.",
            "Drums and percussion driving the groove in a rhythm section.",
            "A drum kit layered with bass in a studio recording.",
            "Percussion layered with a full band in an Afrobeat or Latin production.",
        ],
        "piano_keyboard": [
            "The sound of a piano.",
            "An acoustic or electric keyboard.",
            "A piano playing musical notes.",
            "A bright grand piano with a resonant, hammered tone.",
            "A warm electric piano tone with a bell-like character.",
            "A rich organ tone with a sustained harmonic texture.",
            "A piano playing arpeggiated chords across the keyboard.",
            "A keyboard comping rhythmic jazz chords.",
            "An organ sustaining long, held chords.",
            "Piano accompanying a singer's lead vocal melody.",
            "Keyboard layered with bass and drums in a soul production.",
            "A close-mic piano recording in a studio session.",
        ],
        "strings": [
            "The sound of an orchestral string instrument.",
            "A bowed string instrument such as a violin or cello.",
            "Strings playing musical notes.",
            "A bright, singing violin tone in its upper register.",
            "A deep, warm cello tone in its low register.",
            "A rich string section tone with layered harmonics.",
            "A string instrument played pizzicato with plucked notes.",
            "Strings bowed with long, sustained legato phrases.",
            "A string section playing a fast, rhythmic bowed passage.",
            "A string section layered in an orchestral arrangement.",
            "Strings accompanying a vocalist in a ballad production.",
            "A string quartet layered in a chamber music recording.",
        ],
        "brass": [
            "The sound of a brass instrument.",
            "A trumpet or trombone.",
            "Brass playing musical notes.",
            "A bright, brassy trumpet tone with a sharp edge.",
            "A warm, buzzing trombone tone in its mid register.",
            "A bold brass section tone with layered harmonics.",
            "A brass instrument playing punchy staccato stabs.",
            "A trombone sliding smoothly between notes.",
            "A brass section sustaining a bold harmonized chord.",
            "A brass section layered in a big-band arrangement.",
            "Brass accompanying a vocalist in a soul or funk production.",
            "A close-mic brass recording with studio compression.",
        ],
        "woodwinds": [
            "The sound of a woodwind instrument.",
            "A flute, clarinet, or saxophone.",
            "A woodwind playing musical notes.",
            "A bright, airy flute tone with a breathy edge.",
            "A warm, reedy saxophone tone with a smooth vibrato.",
            "A woody clarinet tone in its middle register.",
            "A woodwind sustaining a smooth legato melodic phrase.",
            "A saxophone honking staccato notes in a funk rhythm.",
            "A flute playing fast, fluttering staccato notes.",
            "A woodwind melody layered over a string orchestra.",
            "Saxophone accompanying a vocalist in an R&B production.",
            "A close-mic woodwind recording in a jazz studio session.",
        ],
        "bass": [
            "The sound of an electric bass guitar.",
            "A low-frequency bass instrument.",
            "A bass guitar playing musical notes.",
            "A deep, round electric bass guitar tone.",
            "A bright, punchy bass guitar with a clicky attack.",
            "A smooth fretless bass guitar with a sliding tone.",
            "Fingerstyle electric bass guitar groove.",
            "Slap bass guitar with percussive pops and snaps.",
            "A picked bass guitar line with syncopated rhythm.",
            "Bass guitar providing the low-end foundation of a rock mix.",
            "Bass guitar locking in with the kick drum in a funk groove.",
            "Bass guitar layered beneath guitars and drums in a studio recording.",
        ],
        "vocals": [
            "The sound of a singing voice.",
            "A male or female vocal.",
            "A vocal performing a melody.",
            "A deep, warm male vocal tone.",
            "A bright, clear female vocal tone with sustained pitch.",
            "A soulful vocal tone with expressive vibrato.",
            "A vocal sustaining a held note with vibrato.",
            "A vocal delivering a rhythmic, syncopated verse.",
            "A vocal belting a powerful high note.",
            "A lead vocal layered over a full band mix.",
            "Vocal harmonies layered in a studio recording.",
            "A close-mic vocal with reverb in a pop production.",
        ],
        "traditional_folk": [
            "The sound of a traditional folk instrument.",
            "A banjo, mandolin, or ukulele.",
            "A folk instrument playing musical notes.",
            "A bright, twangy banjo tone with a metallic edge.",
            "A warm, plucky ukulele tone with a light decay.",
            "A reedy, breathy harmonica tone with a bending pitch.",
            "A banjo playing a fast, rolling bluegrass pattern.",
            "A ukulele strumming bright, rhythmic chords.",
            "A harmonica bending notes in a bluesy phrase.",
            "A folk instrument layered with acoustic guitar in a bluegrass ensemble.",
            "Traditional folk instruments accompanying a vocalist in a country production.",
            "A close-mic folk instrument recording in an acoustic studio session.",
        ],
        "synth": [
            "The sound of a synthesizer.",
            "An electronic synth instrument.",
            "A synthesizer playing musical notes.",
            "A bright, filtered synthesizer lead tone.",
            "A smooth, sustained synthesizer pad texture.",
            "A buzzing analog synthesizer bass tone.",
            "A synthesizer playing a plucky, percussive arpeggio.",
            "A synthesizer sustaining a slow, evolving pad.",
            "A synthesizer lead bending pitch with portamento.",
            "A synthesizer layered with drums in an electronic dance production.",
            "Synthesizer pad accompanying a vocalist in a pop ballad.",
            "A synthesizer bass locked in with a drum machine in a studio mix.",
        ],
    }

    # Conservative initial thresholds; calibrate against labelled audio.
    DEFAULT_MIN_SIMILARITY = 0.22
    DEFAULT_MIN_MARGIN = 0.015

    BASELINE_PROMPTS = [
        "A piece of music with no clearly identifiable individual instrument.",
        "A general music recording.",
    ]

    def __init__(
        self,
        model_loader=None,
        min_similarity=None,
        min_margin=None,
    ):
        self.loader = model_loader or clap_model

        self.min_similarity = (
            self.DEFAULT_MIN_SIMILARITY
            if min_similarity is None
            else float(min_similarity)
        )

        self.min_margin = (
            self.DEFAULT_MIN_MARGIN
            if min_margin is None
            else float(min_margin)
        )

    
    def _load(self):
        """Load CLAP and return its components."""
        print("[CLAP] Checking model availability...", flush=True)

        self.loader.load()

        model = self.loader.model
        processor = self.loader.processor
        device = self.loader.device

        if model is None or processor is None:
            raise RuntimeError(
                "CLAP loader returned without a model and processor."
            )

        print(
            f"[CLAP] Ready. Device={device}; "
            f"model={type(model).__name__}; "
            f"processor={type(processor).__name__}",
            flush=True,
        )

        return model, processor, device


    @staticmethod
    def _normalise_rows(array):
        """L2-normalise each embedding row safely."""
        array = np.asarray(array, dtype=np.float32)
        norms = np.linalg.norm(array, axis=-1, keepdims=True)
        return array / np.maximum(norms, 1e-12)

    
    def _text_embeddings(self, model, processor, device):
        """Build one embedding prototype per instrument and a baseline."""
        import torch

        prompts = []

        for label_prompts in self.instrument_prompts.values():
            prompts.extend(label_prompts)

        prompts.extend(self.BASELINE_PROMPTS)

        print(
            f"[CLAP] Creating text embeddings for "
            f"{len(prompts)} prompts...",
            flush=True,
        )

        inputs = processor(
            text=prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )

        inputs = {
            key: value.to(device)
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            if not hasattr(model, "get_text_features"):
                raise RuntimeError(
                    "Loaded CLAP model does not expose "
                    "get_text_features()."
                )

            text_inputs = {
                key: value
                for key, value in inputs.items()
                if key in {"input_ids", "attention_mask"}
            }

            embeddings = model.get_text_features(**text_inputs)

        embeddings = self._normalise_rows(
            embeddings.detach().cpu().numpy()
        )

        prototypes = {}
        offset = 0

        for label, label_prompts in self.instrument_prompts.items():
            count = len(label_prompts)
            prompt_embeddings = embeddings[offset:offset + count]

            prototype = prompt_embeddings.mean(
                axis=0,
                keepdims=True,
            )

            prototypes[label] = self._normalise_rows(prototype)[0]
            offset += count

        baseline_embeddings = embeddings[offset:]

        baseline = self._normalise_rows(
            baseline_embeddings.mean(axis=0, keepdims=True)
        )[0]

        print(
            f"[CLAP] Text embeddings ready. "
            f"Instrument classes={len(prototypes)}",
            flush=True,
        )

        return prototypes, baseline


    
    def _audio_embedding(self, audio, model, processor, device):
        """Convert audio windows into normalised CLAP embeddings."""
        import torch

        audio = list(audio)

        if not audio:
            raise ValueError(
                "Cannot create CLAP embeddings from an empty batch."
            )

        print(
            f"[CLAP] Preparing {len(audio)} audio windows "
            f"for inference...",
            flush=True,
        )

        inputs = processor(
            audios=audio,
            sampling_rate=self.SAMPLE_RATE,
            return_tensors="pt",
            padding=True,
        )

        inputs = {
            key: value.to(device)
            for key, value in inputs.items()
        }

        print(
            "[CLAP] Audio tensors prepared. Running model inference...",
            flush=True,
        )

        with torch.inference_mode():
            if hasattr(model, "get_audio_features"):
                embedding = model.get_audio_features(**inputs)
            else:
                outputs = model(**inputs)
                embedding = outputs.audio_embeds

        if embedding.ndim == 1:
            embedding = embedding.unsqueeze(0)

        embeddings = self._normalise_rows(
            embedding.detach().cpu().numpy()
        )

        if len(embeddings) != len(audio):
            raise RuntimeError(
                "CLAP returned an unexpected number of audio embeddings. "
                f"Input windows={len(audio)}, "
                f"embeddings={len(embeddings)}."
            )

        print(
            f"[CLAP] Audio inference completed. "
            f"Embeddings={len(embeddings)}",
            flush=True,
        )

        return embeddings


    def _score_embeddings(self, audio_embeddings, prototypes, baseline):
        """Score each instrument relative to generic-music similarity."""
        results = []

        for audio_embedding in audio_embeddings:
            baseline_similarity = float(
                np.dot(audio_embedding, baseline)
            )
            scores = {}

            for label, prototype in prototypes.items():
                similarity = float(np.dot(audio_embedding, prototype))
                evidence = similarity - baseline_similarity

                # Reject weak matches instead of forcing every class positive.
                if (
                    similarity < self.min_similarity
                    or evidence < self.min_margin
                ):
                    score = 0.0
                else:
                    # This is a bounded match index, not a probability.
                    score = float(np.clip(evidence, 0.0, 1.0))

                scores[label] = round(score, 4)

            results.append(scores)

        return results

    
    def detect_batch(
        self,
        windows: Iterable[np.ndarray],
    ) -> List[Dict[str, float]]:
        """Analyze a batch of audio windows using CLAP."""
        windows = list(windows)

        if not windows:
            print("[CLAP] Received an empty batch; skipping.", flush=True)
            return []

        print(
            f"[CLAP] detect_batch() received {len(windows)} windows.",
            flush=True,
        )

        model, processor, device = self._load()

        prototypes, baseline = self._text_embeddings(
            model,
            processor,
            device,
        )

        audio_embeddings = self._audio_embedding(
            windows,
            model,
            processor,
            device,
        )

        print("[CLAP] Calculating instrument scores...", flush=True)

        results = self._score_embeddings(
            audio_embeddings,
            prototypes,
            baseline,
        )

        if len(results) != len(windows):
            raise RuntimeError(
                "CLAP scoring returned an unexpected result count. "
                f"Input windows={len(windows)}, results={len(results)}."
            )

        print(
            f"[CLAP] Batch complete: {len(results)} score dictionaries.",
            flush=True,
        )

        return results


    def detect(self, audio) -> Dict[str, float]:
        """Analyze one audio window."""
        results = self.detect_batch([audio])
        return results[0] if results else {}

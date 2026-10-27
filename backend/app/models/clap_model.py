
from __future__ import annotations

import threading
from typing import Optional


class CLAPModelLoader:
    MODEL_ID = "laion/clap-htsat-unfused"

    def __init__(
        self,
        model=None,
        processor=None,
        device: Optional[str] = None,
    ):
        self.model = model
        self.processor = processor
        self.device = device
        self._lock = threading.Lock()

    def load(self):
        # Reuse the already-loaded model.
        if self.model is not None and self.processor is not None:
            print(
                f"[CLAP] Model already loaded on {self.device}.",
                flush=True,
            )
            return self

        with self._lock:
            # Check again after acquiring the lock.
            if self.model is not None and self.processor is not None:
                return self

            print("[CLAP] Initializing model loader...", flush=True)

            try:
                import torch
                from transformers import ClapModel, ClapProcessor
            except ImportError as exc:
                raise RuntimeError(
                    "CLAP dependencies are missing. Install the "
                    "dependencies from backend/requirements.txt "
                    "in the active Python environment."
                ) from exc

            self.device = self.device or (
                "cuda" if torch.cuda.is_available() else "cpu"
            )

            print(f"[CLAP] Selected device: {self.device}", flush=True)
            print(
                f"[CLAP] Loading processor: {self.MODEL_ID}",
                flush=True,
            )

            self.processor = ClapProcessor.from_pretrained(
                self.MODEL_ID
            )

            print(
                "[CLAP] Processor loaded. Loading model weights...",
                flush=True,
            )

            self.model = ClapModel.from_pretrained(
                self.MODEL_ID
            ).to(self.device)

            self.model.eval()

            print(
                f"[CLAP] Model loaded successfully on {self.device}.",
                flush=True,
            )

        return self


clap_model = CLAPModelLoader()

import torch
from transformers import ClapModel, ClapProcessor


class CLAPModelLoader:

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Loading CLAP model on {self.device}...")

        self.processor = ClapProcessor.from_pretrained(
            "laion/clap-htsat-unfused"
        )

        self.model = ClapModel.from_pretrained(
            "laion/clap-htsat-unfused"
        ).to(self.device)

        self.model.eval()

        print("CLAP model loaded successfully.")


clap_model = CLAPModelLoader()
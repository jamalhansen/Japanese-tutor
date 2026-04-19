import os
from pathlib import Path
from typing import Optional
from unstract.llmwhisperer import LLMWhispererClientV2


class OCRError(Exception):
    """Raised when OCR extraction fails."""


class OCRClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("LLMWHISPERER_API_KEY")
        self.base_url = base_url or os.environ.get(
            "LLMWHISPERER_BASE_URL_V2",
            "https://llmwhisperer-api.us-central.unstract.com/api/v2",
        )

        if not self.api_key:
            raise RuntimeError("LLMWHISPERER_API_KEY is required.")

        self.client = LLMWhispererClientV2(api_key=self.api_key, base_url=self.base_url)

    def extract_text(self, image_path: Path) -> str:
        """Extract text from image using LLMWhisperer in high_quality mode."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found at {image_path}")

        try:
            # Sync extraction for small textbook pages
            result = self.client.whisper(
                file_path=str(image_path),
                wait_for_completion=True,
                wait_timeout=200,
                mode="high_quality",
                output_mode="layout_preserving",
            )
            return result.get("extracted_text", "")
        except Exception as e:
            raise OCRError(f"LLMWhisperer OCR failed: {e}") from e

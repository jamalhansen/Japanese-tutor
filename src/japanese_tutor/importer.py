import logging
from pathlib import Path
from typing import List, Literal, Optional, Type, Union

from local_first_common.tracking import timed_run
from local_first_common.providers.base import BaseProvider
from pydantic import BaseModel

from .ocr import OCRClient
from .prompts import (
    get_extraction_system_prompt,
    get_suitability_system_prompt,
    get_user_prompt,
)
from .schema import GrammarCard, KanjiCard, ReviewResult, VocabularyCard

logger = logging.getLogger(__name__)

class TutorLogic:
    def __init__(self, provider: BaseProvider, ocr_client: Optional[OCRClient] = None):
        self.provider = provider
        self.ocr_client = ocr_client or OCRClient()

    def check_suitability(self, image_path: Path) -> ReviewResult:
        """Use Gemini (Vision) to check if the image is a valid Japanese textbook page."""
        system = get_suitability_system_prompt()
        user = "Is this image suitable for Japanese flashcard extraction?"
        
        # We need an image-capable model for this. 
        # local-first-common GeminiProvider handles images if passed.
        with timed_run("japanese-tutor", self.provider.model, source_location=str(image_path)) as _run:
            # Read image as bytes
            with open(image_path, "rb") as f:
                img_data = f.read()
            
            raw_result = self.provider.complete(
                system=system,
                user=user,
                response_model=ReviewResult,
                images=[img_data]
            )
            result = ReviewResult.model_validate(raw_result)
            _run.item_count = 1
            return result

    def process_image(
        self,
        image_path: Path,
        mode: Literal["vocabulary", "kanji", "grammar"],
        custom_instructions: str = ""
    ) -> List[Union[VocabularyCard, KanjiCard, GrammarCard]]:
        """Main workflow: Suitability -> OCR -> Extraction."""
        
        # 1. Suitability Check
        review = self.check_suitability(image_path)
        if review.suitability == "fail":
            logger.warning(f"Image suitability failed: {review.reason}")
            return []

        # 2. OCR
        logger.info(f"Extracting text from {image_path} using LLMWhisperer...")
        ocr_text = self.ocr_client.extract_text(image_path)
        if not ocr_text:
            logger.warning("No text extracted from image.")
            return []

        # 3. Extraction
        schema_map: dict[str, Type[BaseModel]] = {
            "vocabulary": VocabularyCard,
            "kanji": KanjiCard,
            "grammar": GrammarCard,
        }
        
        # The LLM often needs to return a LIST of these objects.
        # We'll wrap the schema in a list container if needed, or just ask for a list.
        # For now, let's assume the provider can handle a List[T] if we define it.
        # Actually, let's define a wrapper schema for the list.
        
        class CardList(BaseModel):
            cards: List[schema_map[mode]] # type: ignore

        system = get_extraction_system_prompt(mode)
        user = get_user_prompt(ocr_text, custom_instructions)
        
        logger.info(f"Extracting {mode} data using LLM...")
        with timed_run("japanese-tutor", self.provider.model, source_location=str(image_path)) as _run:
            raw_result = self.provider.complete(
                system=system,
                user=user,
                response_model=CardList
            )
            result = CardList.model_validate(raw_result)
            _run.item_count = len(result.cards)
            return result.cards

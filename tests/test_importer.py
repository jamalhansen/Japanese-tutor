"""Tests for TutorLogic's image-handling in importer.py."""
import base64
import json
from unittest.mock import MagicMock

from local_first_common.testing import MockProvider

from japanese_tutor.importer import TutorLogic


class TestCheckSuitabilityImageEncoding:
    def test_image_is_base64_encoded_before_being_sent_to_provider(self, tmp_path):
        """Every provider's images= expects a base64 string, not raw file bytes --
        GatewayProvider in particular has to fit it into a JSON request body."""
        raw_bytes = b"\x89PNG\r\n\x1a\nfakepngdata"
        image_path = tmp_path / "page.png"
        image_path.write_bytes(raw_bytes)

        provider = MagicMock()
        provider.model = "test-model"
        provider.complete.return_value = {
            "suitability": "pass",
            "reason": None,
            "post_type": "vocabulary",
            "word_count": 12,
            "summary": "Looks fine.",
        }

        logic = TutorLogic(provider=provider, ocr_client=MagicMock())
        logic.check_suitability(image_path)

        _, kwargs = provider.complete.call_args
        sent_images = kwargs["images"]
        assert len(sent_images) == 1
        assert isinstance(sent_images[0], str)
        assert base64.b64decode(sent_images[0]) == raw_bytes


class TestCheckSuitabilitySourceLocation:
    """Regression 2026-09-20: an LLM call is logged once, inside the
    gateway. check_suitability used to keep its own duplicate processing_log
    row via timed_run(); source_location/item_count now travel to the
    gateway via self.provider instead."""

    def test_source_location_and_item_count_set_before_the_call(self, tmp_path):
        image_path = tmp_path / "page.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\nfakepngdata")

        llm = MockProvider(
            response=json.dumps(
                {
                    "suitability": "pass",
                    "reason": None,
                    "post_type": "vocabulary",
                    "word_count": 12,
                    "summary": "Looks fine.",
                }
            )
        )

        TutorLogic(provider=llm, ocr_client=MagicMock()).check_suitability(image_path)

        assert llm.source_location == str(image_path)
        assert llm.item_count == 1

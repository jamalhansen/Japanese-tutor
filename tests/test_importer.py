"""Tests for TutorLogic's image-handling in importer.py."""
import base64
import json
from unittest.mock import MagicMock

import duckdb
from local_first_common.testing import MockProvider
from local_first_common.tracking import get_tracking_db_path

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


class TestCheckSuitabilityModelLoggedAfterResolution:
    """Regression 2026-09-20: this row was one of the real ones showing up
    with an empty model in production. llm.model was captured for
    timed_run() before self.provider.complete() resolved it -- re-read it
    post-call, same fix as LLMHelper's 3 methods."""

    def test_model_and_provider_reflect_post_resolution_value(self, tmp_path):
        image_path = tmp_path / "page.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\nfakepngdata")

        class ResolvesModelDuringCall(MockProvider):
            default_model = ""  # matches GatewayProvider's own real default when no model is specified

            def _complete(self, system, user, response_model=None, images=None):
                result = super()._complete(system, user, response_model, images)
                self.model = "phi4-mini"  # simulates the gateway resolving an unspecified model
                return result

        llm = ResolvesModelDuringCall(
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
        assert llm.model == ""

        TutorLogic(provider=llm, ocr_client=MagicMock()).check_suitability(image_path)

        conn = duckdb.connect(str(get_tracking_db_path()))
        row = conn.execute(
            "SELECT model, provider FROM processing_log WHERE tool_name = 'japanese-tutor' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row[0] == "phi4-mini"
        assert row[1] == "mock"

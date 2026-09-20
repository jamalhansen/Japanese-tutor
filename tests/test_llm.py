"""Regression 2026-09-20: japanese-tutor's own processing_log rows showed up
with an empty model whenever routed through the gateway with no explicit
--model (LLM_GATEWAY_URL is exported globally, so this is the fleet-wide
default path). Root cause: llm.model was captured for timed_run() before
self.provider.complete() resolved it. Re-read self.provider.model/provider_name
inside each block, after the call, for all 3 LLMHelper methods. Each test
here mutates .model *inside* _complete() (not before construction) to prove
the value is re-read post-call, not just captured lucky at construction time.
"""
import duckdb
from local_first_common.testing import MockProvider
from local_first_common.tracking import get_tracking_db_path

from japanese_tutor.llm import LLMHelper


def _resolving_provider(response):
    class ResolvesModelDuringCall(MockProvider):
        default_model = ""  # matches GatewayProvider's own real default when no model is specified

        def _complete(self, system, user, response_model=None, images=None):
            result = super()._complete(system, user, response_model, images)
            self.model = "phi4-mini"  # simulates the gateway resolving an unspecified model
            return result

    return ResolvesModelDuringCall(response=response)


def _last_row():
    conn = duckdb.connect(str(get_tracking_db_path()))
    row = conn.execute(
        "SELECT model, provider FROM processing_log WHERE tool_name = 'japanese-tutor' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row


def test_generate_mnemonics_logs_the_model_resolved_after_the_call():
    llm = _resolving_provider('{"suggestions": [{"body": "a mnemonic"}]}')
    assert llm.model == ""
    helper = LLMHelper(llm)

    result = helper.generate_mnemonics("あ", "a")

    assert result == ["a mnemonic"]
    row = _last_row()
    assert row[0] == "phi4-mini"
    assert row[1] == "mock"


def test_generate_adaptive_example_logs_the_model_resolved_after_the_call():
    llm = _resolving_provider("こんにちは")
    helper = LLMHelper(llm)

    helper.generate_adaptive_example("あ", ["こんにちは"])

    row = _last_row()
    assert row[0] == "phi4-mini"
    assert row[1] == "mock"


def test_generate_session_debrief_logs_the_model_resolved_after_the_call():
    llm = _resolving_provider("Good session overall.")
    helper = LLMHelper(llm)

    helper.generate_session_debrief(["あ"], ["い"])

    row = _last_row()
    assert row[0] == "phi4-mini"
    assert row[1] == "mock"

"""Regression 2026-09-20: an LLM call is logged once, inside the gateway --
japanese-tutor used to keep its own duplicate processing_log row via
timed_run(), re-reading self.provider.model/provider_name after the call to
work around a GatewayProvider's model resolving mid-call. That workaround
is gone along with the second write; source_location now travels to the
gateway via self.provider.source_location instead, set before the call
(item_count is dropped where it depended on the response, like the number
of mnemonics returned -- unknowable before the request is sent).
"""
from local_first_common.testing import MockProvider

from japanese_tutor.llm import LLMHelper


def test_generate_mnemonics_sets_source_location_before_the_call():
    llm = MockProvider(response='{"suggestions": [{"body": "a mnemonic"}]}')
    helper = LLMHelper(llm)

    result = helper.generate_mnemonics("あ", "a")

    assert result == ["a mnemonic"]
    assert llm.source_location == "mnemonic:あ"


def test_generate_adaptive_example_sets_source_location_before_the_call():
    llm = MockProvider(response="こんにちは")
    helper = LLMHelper(llm)

    helper.generate_adaptive_example("あ", ["こんにちは"])

    assert llm.source_location == "example:あ"
    assert llm.item_count == 1


def test_generate_session_debrief_sets_source_location_before_the_call():
    llm = MockProvider(response="Good session overall.")
    helper = LLMHelper(llm)

    helper.generate_session_debrief(["あ"], ["い"])

    assert llm.source_location == "session_debrief"
    assert llm.item_count == 1

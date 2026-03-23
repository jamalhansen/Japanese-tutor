from typing import List
from pydantic import BaseModel
from local_first_common.providers.base import BaseProvider
from local_first_common.tracking import timed_run

class MnemonicSuggestion(BaseModel):
    body: str

class MnemonicList(BaseModel):
    suggestions: List[MnemonicSuggestion]

class LLMHelper:
    def __init__(self, provider: BaseProvider):
        self.provider = provider

    def generate_mnemonics(self, character: str, romaji: str) -> List[str]:
        system = (
            "You are a Japanese language learning assistant. "
            "Generate 3 creative visual mnemonics to help a student remember the "
            "reading of a Japanese character."
        )
        user = (
            f"Character: {character}\n"
            f"Reading: {romaji}\n\n"
            "Provide 3 short, catchy mnemonics. Each should be one sentence."
        )

        with timed_run("japanese-tutor", self.provider.model, source_location=f"mnemonic:{character}") as _run:
            result = self.provider.complete(
                system=system,
                user=user,
                response_model=MnemonicList
            )
            _run.item_count = len(result.suggestions)
            return [s.body for s in result.suggestions]

    def generate_adaptive_example(self, character: str, mastered_vocab: List[str]) -> str:
        system = (
            "You are a Japanese language tutor. Generate a simple example sentence "
            "using the provided character. Use ONLY the vocabulary from the mastered list "
            "where possible. If essential particles or grammar are needed, keep them basic."
        )
        vocab_text = ", ".join(mastered_vocab)
        user = f"Character: {character}\nMastered Vocabulary: {vocab_text}\n\nGenerate one short example sentence."

        with timed_run("japanese-tutor", self.provider.model, source_location=f"example:{character}") as _run:
            result = self.provider.complete(system=system, user=user)
            _run.item_count = 1
            return result

    def generate_session_debrief(self, missed_chars: List[str], recurring_chars: List[str]) -> str:
        system = (
            "You are a supportive Japanese tutor. Analyze the user's mistakes from "
            "their last study session. Provide a 2-3 sentence debrief with actionable "
            "observations or memory hooks for the characters they are confusing."
        )
        missed = ", ".join(missed_chars)
        recurring = ", ".join(recurring_chars)
        user = f"Missed this session: {missed}\nRecurringly missed: {recurring}"

        with timed_run("japanese-tutor", self.provider.model, source_location="session_debrief") as _run:
            result = self.provider.complete(system=system, user=user)
            _run.item_count = 1
            return result

from japanese_tutor.schema import VocabularyCard, KanjiCard, GrammarCard
from japanese_tutor.characters import HIRAGANA, KATAKANA, KANJI_N5

def test_schema_instantiation():
    v = VocabularyCard(kanji="猫", furigana="ねこ", english="cat")
    assert v.kanji == "猫"
    
    k = KanjiCard(character="日", meaning="day", examples=["日本"])
    assert k.character == "日"
    
    g = GrammarCard(pattern="~は~です", explanation="Basic polite copula")
    assert g.pattern == "~は~です"

def test_characters_data():
    assert len(HIRAGANA) == 46
    assert len(KATAKANA) == 46
    assert len(KANJI_N5) > 0
    assert HIRAGANA[0]["char"] == "あ"

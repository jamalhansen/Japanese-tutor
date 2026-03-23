from typing import TypedDict, Optional

class CharacterInfo(TypedDict):
    char: str
    romaji: str
    stage: str
    meaning: Optional[str]

# Full 46 Hiragana
HIRAGANA = [
    {"char": "あ", "romaji": "a", "stage": "hiragana"}, {"char": "い", "romaji": "i", "stage": "hiragana"},
    {"char": "う", "romaji": "u", "stage": "hiragana"}, {"char": "え", "romaji": "e", "stage": "hiragana"},
    {"char": "お", "romaji": "o", "stage": "hiragana"},
    {"char": "か", "romaji": "ka", "stage": "hiragana"}, {"char": "き", "romaji": "ki", "stage": "hiragana"},
    {"char": "く", "romaji": "ku", "stage": "hiragana"}, {"char": "け", "romaji": "ke", "stage": "hiragana"},
    {"char": "こ", "romaji": "ko", "stage": "hiragana"},
    {"char": "さ", "romaji": "sa", "stage": "hiragana"}, {"char": "し", "romaji": "shi", "stage": "hiragana"},
    {"char": "す", "romaji": "su", "stage": "hiragana"}, {"char": "せ", "romaji": "se", "stage": "hiragana"},
    {"char": "そ", "romaji": "so", "stage": "hiragana"},
    {"char": "た", "romaji": "ta", "stage": "hiragana"}, {"char": "ち", "romaji": "chi", "stage": "hiragana"},
    {"char": "つ", "romaji": "tsu", "stage": "hiragana"}, {"char": "て", "romaji": "te", "stage": "hiragana"},
    {"char": "と", "romaji": "to", "stage": "hiragana"},
    {"char": "な", "romaji": "na", "stage": "hiragana"}, {"char": "に", "romaji": "ni", "stage": "hiragana"},
    {"char": "ぬ", "romaji": "nu", "stage": "hiragana"}, {"char": "ね", "romaji": "ne", "stage": "hiragana"},
    {"char": "の", "romaji": "no", "stage": "hiragana"},
    {"char": "は", "romaji": "ha", "stage": "hiragana"}, {"char": "ひ", "romaji": "hi", "stage": "hiragana"},
    {"char": "ふ", "romaji": "fu", "stage": "hiragana"}, {"char": "へ", "romaji": "he", "stage": "hiragana"},
    {"char": "ほ", "romaji": "ho", "stage": "hiragana"},
    {"char": "ま", "romaji": "ma", "stage": "hiragana"}, {"char": "み", "romaji": "mi", "stage": "hiragana"},
    {"char": "む", "romaji": "mu", "stage": "hiragana"}, {"char": "め", "romaji": "me", "stage": "hiragana"},
    {"char": "も", "romaji": "mo", "stage": "hiragana"},
    {"char": "や", "romaji": "ya", "stage": "hiragana"}, {"char": "ゆ", "romaji": "yu", "stage": "hiragana"},
    {"char": "よ", "romaji": "yo", "stage": "hiragana"},
    {"char": "ら", "romaji": "ra", "stage": "hiragana"}, {"char": "り", "romaji": "ri", "stage": "hiragana"},
    {"char": "る", "romaji": "ru", "stage": "hiragana"}, {"char": "れ", "romaji": "re", "stage": "hiragana"},
    {"char": "ろ", "romaji": "ro", "stage": "hiragana"},
    {"char": "わ", "romaji": "wa", "stage": "hiragana"}, {"char": "を", "romaji": "wo", "stage": "hiragana"},
    {"char": "ん", "romaji": "n", "stage": "hiragana"}
]

# Full 46 Katakana
KATAKANA = [
    {"char": "ア", "romaji": "a", "stage": "katakana"}, {"char": "イ", "romaji": "i", "stage": "katakana"},
    {"char": "ウ", "romaji": "u", "stage": "katakana"}, {"char": "エ", "romaji": "e", "stage": "katakana"},
    {"char": "オ", "romaji": "o", "stage": "katakana"},
    {"char": "カ", "romaji": "ka", "stage": "katakana"}, {"char": "キ", "romaji": "ki", "stage": "katakana"},
    {"char": "ク", "romaji": "ku", "stage": "katakana"}, {"char": "ケ", "romaji": "ke", "stage": "katakana"},
    {"char": "コ", "romaji": "ko", "stage": "katakana"},
    {"char": "サ", "romaji": "sa", "stage": "katakana"}, {"char": "シ", "romaji": "shi", "stage": "katakana"},
    {"char": "ス", "romaji": "su", "stage": "katakana"}, {"char": "セ", "romaji": "se", "stage": "katakana"},
    {"char": "ソ", "romaji": "so", "stage": "katakana"},
    {"char": "タ", "romaji": "ta", "stage": "katakana"}, {"char": "チ", "romaji": "chi", "stage": "katakana"},
    {"char": "ツ", "romaji": "tsu", "stage": "katakana"}, {"char": "テ", "romaji": "te", "stage": "katakana"},
    {"char": "ト", "romaji": "to", "stage": "katakana"},
    {"char": "ナ", "romaji": "na", "stage": "katakana"}, {"char": "ニ", "romaji": "ni", "stage": "katakana"},
    {"char": "ヌ", "romaji": "nu", "stage": "katakana"}, {"char": "ネ", "romaji": "ne", "stage": "katakana"},
    {"char": "ノ", "romaji": "no", "stage": "katakana"},
    {"char": "ハ", "romaji": "ha", "stage": "katakana"}, {"char": "ヒ", "romaji": "hi", "stage": "katakana"},
    {"char": "フ", "romaji": "fu", "stage": "katakana"}, {"char": "ヘ", "romaji": "he", "stage": "katakana"},
    {"char": "ホ", "romaji": "ho", "stage": "katakana"},
    {"char": "マ", "romaji": "ma", "stage": "katakana"}, {"char": "ミ", "romaji": "mi", "stage": "katakana"},
    {"char": "ム", "romaji": "mu", "stage": "katakana"}, {"char": "メ", "romaji": "me", "stage": "katakana"},
    {"char": "モ", "romaji": "mo", "stage": "katakana"},
    {"char": "ヤ", "romaji": "ya", "stage": "katakana"}, {"char": "ユ", "romaji": "yu", "stage": "katakana"},
    {"char": "ヨ", "romaji": "yo", "stage": "katakana"},
    {"char": "ラ", "romaji": "ra", "stage": "katakana"}, {"char": "リ", "romaji": "ri", "stage": "katakana"},
    {"char": "ル", "romaji": "ru", "stage": "katakana"}, {"char": "レ", "romaji": "re", "stage": "katakana"},
    {"char": "ロ", "romaji": "ro", "stage": "katakana"},
    {"char": "ワ", "romaji": "wa", "stage": "katakana"}, {"char": "ヲ", "romaji": "wo", "stage": "katakana"},
    {"char": "ン", "romaji": "n", "stage": "katakana"}
]

# Basic N5 Kanji Sample
KANJI_N5 = [
    {"char": "一", "romaji": "ichi", "stage": "kanji", "meaning": "one"},
    {"char": "二", "romaji": "ni", "stage": "kanji", "meaning": "two"},
    {"char": "三", "romaji": "san", "stage": "kanji", "meaning": "three"},
    {"char": "日", "romaji": "hi/nichi", "stage": "kanji", "meaning": "day/sun"},
    {"char": "月", "romaji": "tsuki/getsu", "stage": "kanji", "meaning": "month/moon"},
]

HIRAGANA_ROWS = [
    ["あ", "い", "う", "え", "お"], ["か", "き", "く", "け", "こ"],
    ["さ", "し", "す", "せ", "そ"], ["た", "ち", "つ", "て", "と"],
    ["な", "に", "ぬ", "ね", "の"], ["は", "ひ", "ふ", "へ", "ほ"],
    ["ま", "み", "む", "め", "も"], ["や", "ゆ", "よ"],
    ["ら", "り", "る", "れ", "ろ"], ["わ", "を", "ん"],
]

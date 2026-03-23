from typing import Literal

def get_suitability_system_prompt() -> str:
    return (
        "You are an expert Japanese language educator and document analyst.\n"
        "Your task is to determine if the provided image contains Japanese textbook content suitable for flashcard extraction.\n"
        "Analyze the image for: Japanese characters (Kanji, Hiragana, Katakana), vocabulary lists, grammar explanations, or Kanji practice sections.\n"
        "Respond only with a JSON object matching the ReviewResult schema."
    )

def get_extraction_system_prompt(mode: Literal["vocabulary", "kanji", "grammar"]) -> str:
    role = "You are a Japanese language expert specializing in curriculum design and Anki flashcard creation.\n"
    
    context = (
        f"You will be provided with OCR text from a Japanese textbook page. Your goal is to extract {mode} "
        "and structure it for flashcards. Use any visual context clues from the layout preservation "
        "(like columns, headers, or bolded terms) to group related items.\n\n"
        "Ensure all Kanji has appropriate Furigana where possible. For Grammar, ensure the explanation "
        "is clear and captures usage nuances. For Kanji, provide both On-yomi and Kun-yomi readings."
    )
    
    constraints = (
        "\n\nConstraints:\n"
        "- Return ONLY valid JSON.\n"
        "- Do not include preamble or conversational filler.\n"
        "- If the text is ambiguous, make a best-effort guess based on common textbook patterns."
    )
    
    return role + context + constraints

def get_user_prompt(ocr_text: str, custom_instructions: str = "") -> str:
    prompt = f"OCR Text:\n---\n{ocr_text}\n---\n"
    if custom_instructions:
        prompt += f"\nCustom Instructions: {custom_instructions}\n"
    return prompt

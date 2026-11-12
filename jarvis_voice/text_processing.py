QUESTION_STARTS = {
    "где",
    "зачем",
    "как",
    "какой",
    "когда",
    "кто",
    "можно",
    "почему",
    "сколько",
    "что",
}


def punctuate_text(text: str) -> str:
    text = " ".join(text.split()).strip()
    if not text:
        return text

    text = text[0].upper() + text[1:]
    if text.endswith((".", "!", "?", "…")):
        return text

    first_word = text.split(maxsplit=1)[0].lower().replace("ё", "е")
    return text + ("?" if first_word in QUESTION_STARTS else ".")


def extract_local_question(text: str) -> str | None:
    normalized = " ".join(text.split()).strip()
    prefix = "спроси"
    if not normalized.lower().replace("ё", "е").startswith(prefix):
        return None
    if len(normalized) > len(prefix) and not normalized[len(prefix)].isspace():
        return None
    return normalized[len(prefix):].strip()

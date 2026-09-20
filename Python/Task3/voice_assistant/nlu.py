"""
nlu.py
------
Very small natural-language-understanding layer.

Instead of only matching hard-coded keywords, this module extracts an
(intent, entities) pair from a free-form spoken sentence, e.g.:

    "hey can you email john about tomorrow's meeting"
        -> intent="send_email", entities={"raw": "...", "about": "tomorrow's meeting"}

    "what's the weather like in london right now"
        -> intent="get_weather", entities={"city": "london"}

    "remind me to check the oven in ten minutes"
        -> intent="set_reminder", entities={"message": "check the oven", "minutes": 10}

Design notes
------------
This is intentionally dependency-light (regex + keyword scoring) so the
project runs out of the box. If `nltk` is installed, we use it to tokenize
and lemmatize text, which makes matching a little more robust to word
endings ("emailing" -> "email"). If it isn't installed, or its data isn't
downloaded, we transparently fall back to plain string matching -- nothing
breaks either way.

For a stronger NLU layer, swap `parse_intent` for a call to a
`transformers` zero-shot-classification pipeline or an intent-classification
model; the rest of the assistant only depends on the (intent, entities)
contract below, so that swap is isolated to this file.
"""

import re

try:
    import nltk
    from nltk.stem import WordNetLemmatizer

    _lemmatizer = WordNetLemmatizer()

    def _normalize(text: str) -> str:
        try:
            tokens = nltk.word_tokenize(text)
            return " ".join(_lemmatizer.lemmatize(t) for t in tokens)
        except LookupError:
            # nltk data (punkt/wordnet) not downloaded -> fall back
            return text

except ImportError:  # nltk not installed at all

    def _normalize(text: str) -> str:
        return text


INTENT_KEYWORDS = {
    "greet": ["hello", "hi", "hey"],
    "get_time": ["time"],
    "get_date": ["date"],
    "web_search": ["search", "look up", "google"],
    "send_email": ["email", "mail"],
    "set_reminder": ["remind", "reminder", "alert me"],
    "get_weather": ["weather", "temperature", "forecast", "rain"],
    "ask_knowledge": ["who is", "what is", "what are", "tell me about", "define"],
    "add_command": ["add a command", "new command", "create a command"],
    "exit": ["exit", "quit", "stop", "goodbye", "bye"],
}


def parse_intent(text: str) -> tuple[str, dict]:
    """Return (intent_name, entities_dict) for a spoken sentence."""
    normalized = _normalize(text.lower())

    # Score each intent by how many of its keywords appear; pick the best.
    best_intent, best_score = "unknown", 0
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in normalized)
        if score > best_score:
            best_intent, best_score = intent, score

    entities = _extract_entities(best_intent, text)
    return best_intent, entities


def _extract_entities(intent: str, text: str) -> dict:
    lowered = text.lower()

    if intent == "web_search":
        topic = re.sub(r".*(search for|search|look up|google)", "", lowered, count=1)
        return {"query": topic.strip()}

    if intent == "send_email":
        # "email john saying I'm running late" / "send an email to john about the report"
        to_match = re.search(r"(?:to|email)\s+([a-zA-Z0-9_. ]+?)(?:\s+(?:about|saying|that)\s+|$)", lowered)
        body_match = re.search(r"(?:about|saying|that)\s+(.*)", lowered)
        return {
            "to": to_match.group(1).strip() if to_match else "",
            "body": body_match.group(1).strip() if body_match else "",
        }

    if intent == "set_reminder":
        time_match = re.search(r"in\s+(\d+)\s*(second|minute|hour)s?", lowered)
        message_match = re.search(r"remind me to (.*?)(?:\s+in\s+\d+|$)", lowered)
        amount = int(time_match.group(1)) if time_match else None
        unit = time_match.group(2) if time_match else None
        return {
            "message": message_match.group(1).strip() if message_match else "your reminder",
            "amount": amount,
            "unit": unit,
        }

    if intent == "get_weather":
        city_match = re.search(r"(?:in|for)\s+([a-zA-Z ]+)$", lowered)
        return {"city": city_match.group(1).strip() if city_match else None}

    if intent == "ask_knowledge":
        topic = re.sub(r".*(who is|what is|what are|tell me about|define)", "", lowered, count=1)
        return {"topic": topic.strip(" ?")}

    if intent == "add_command":
        return {"raw": lowered}

    return {}

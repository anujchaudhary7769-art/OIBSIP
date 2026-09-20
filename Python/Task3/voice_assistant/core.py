"""
core.py
-------
Shared building blocks used by both beginner_assistant.py and advanced_assistant.py:

- speak(text)        : text-to-speech output (pyttsx3)
- listen()           : microphone capture -> text (speech_recognition), with
                        graceful error handling for unclear / unheard audio
- get_time_date()    : current time and date as spoken-friendly strings
- web_search(query)  : opens a browser search for the given query

Keeping these in one place means the beginner and advanced scripts stay in
sync and you only have to fix a bug (e.g. a microphone quirk) once.
"""

import datetime
import webbrowser

import pyttsx3
import speech_recognition as sr

# ---------------------------------------------------------------------------
# Text-to-speech
# ---------------------------------------------------------------------------

_engine = None


def _get_engine():
    """Lazily create a single pyttsx3 engine instance (re-creating it on
    every call can crash on some platforms/drivers)."""
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 175)  # a bit slower than default = clearer
    return _engine


def speak(text: str) -> None:
    """Speak `text` out loud and also print it, so the assistant is usable
    even with speakers off / for debugging."""
    print(f"Assistant: {text}")
    engine = _get_engine()
    engine.say(text)
    engine.runAndWait()


# ---------------------------------------------------------------------------
# Speech-to-text
# ---------------------------------------------------------------------------

_recognizer = sr.Recognizer()


def listen(timeout: int = 5, phrase_time_limit: int = 8) -> str | None:
    """
    Capture audio from the default microphone and return the recognized
    text (lowercased), or None if nothing usable was heard.

    Handles the three common failure modes gracefully instead of crashing:
      - no speech detected before `timeout`      -> sr.WaitTimeoutError
      - speech detected but not understood       -> sr.UnknownValueError
      - the recognition API/service failed       -> sr.RequestError
    """
    try:
        with sr.Microphone() as source:
            print("Listening...")
            _recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = _recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
    except sr.WaitTimeoutError:
        speak("I didn't hear anything. Could you say that again?")
        return None
    except OSError:
        # Typically "no microphone found" - fatal for this call, but we let
        # the caller decide what to do rather than crashing the process.
        speak("I couldn't access a microphone. Please check your audio setup.")
        return None

    try:
        text = _recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that. Could you please repeat?")
        return None
    except sr.RequestError:
        speak("Speech recognition service is unavailable right now.")
        return None


# ---------------------------------------------------------------------------
# Simple built-in features shared by both tiers
# ---------------------------------------------------------------------------


def get_time_date() -> tuple[str, str]:
    """Return (time_string, date_string) suitable for speaking aloud."""
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d, %Y")
    return time_str, date_str


def web_search(query: str) -> str:
    """Open the default browser with a Google search for `query`.
    Returns the confirmation message spoken to the user."""
    query = query.strip()
    if not query:
        return "I didn't catch what you wanted me to search for."
    from urllib.parse import quote_plus

    url = f"https://www.google.com/search?q={quote_plus(query)}"
    webbrowser.open(url)
    return f"Here's what I found for {query}."

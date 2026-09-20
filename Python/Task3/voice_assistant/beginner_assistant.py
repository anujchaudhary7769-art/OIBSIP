"""
beginner_assistant.py
----------------------
Beginner-tier voice assistant.

Checklist covered:
  [x] Capture voice input using speech_recognition (microphone)
  [x] Respond to "Hello" with a predefined greeting
  [x] Tell the current time and date on request
  [x] Perform a web search on a user-specified topic
  [x] Graceful error handling: if voice is not understood, ask to repeat
  [x] Text-to-speech feedback using pyttsx3 for all responses

Run with:
    python beginner_assistant.py

Say "exit", "quit", or "stop" to end the program.
"""

from core import speak, listen, get_time_date, web_search

EXIT_WORDS = {"exit", "quit", "stop", "goodbye", "bye"}


def handle_command(command: str) -> bool:
    """
    Match `command` (already lowercased text from listen()) against the
    beginner feature set using simple keyword matching.

    Returns False if the assistant should shut down, True otherwise.
    """
    if any(word in command for word in EXIT_WORDS):
        speak("Goodbye!")
        return False

    if "hello" in command or "hi " in command or command.strip() == "hi":
        speak("Hello! How can I help you today?")

    elif "time" in command and "date" in command:
        time_str, date_str = get_time_date()
        speak(f"It's currently {time_str}, on {date_str}.")

    elif "time" in command:
        time_str, _ = get_time_date()
        speak(f"It's currently {time_str}.")

    elif "date" in command:
        _, date_str = get_time_date()
        speak(f"Today's date is {date_str}.")

    elif "search" in command:
        # e.g. "search for python tutorials" / "search python tutorials"
        topic = command.split("search", 1)[1]
        topic = topic.replace(" for ", "", 1).strip()
        message = web_search(topic)
        speak(message)

    else:
        speak(
            "I can say hello, tell you the time or date, or search the web. "
            "Try one of those!"
        )

    return True


def main() -> None:
    speak("Voice assistant ready. Say hello, ask for the time or date, "
          "or ask me to search something.")

    running = True
    while running:
        command = listen()
        if command is None:
            # listen() already asked the user to repeat / spoke the error
            continue
        running = handle_command(command)


if __name__ == "__main__":
    main()

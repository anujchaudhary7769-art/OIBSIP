"""
advanced_assistant.py
-----------------------
Advanced-tier voice assistant. Includes everything in beginner_assistant.py,
plus:

  [x] Natural language understanding (nlu.py)          -> free-form sentences,
      not just fixed keywords
  [x] Send an email via voice command (integrations.py + smtplib)
  [x] Timed reminders with an audible alert (reminders.py)
  [x] Live weather via OpenWeatherMap (integrations.py)
  [x] General knowledge Q&A via Wikipedia summary API (integrations.py)
  [x] User-addable custom commands, via config.json or by voice
      (custom_commands.py)
  [x] Privacy notes: see README.md

Run with:
    python advanced_assistant.py

Say "exit", "quit", or "stop" to end the program.

Setup required for the advanced features (weather/email) is documented in
README.md - the assistant still works for time/date/search/greetings/QA/
reminders/custom commands without any of that configuration.
"""

from core import speak, listen, get_time_date, web_search
from nlu import parse_intent
from integrations import get_weather, ask_knowledge, send_email
from reminders import set_reminder
from custom_commands import load_config, match_custom_command, add_custom_command

import webbrowser


def handle_add_command_flow() -> str:
    """Walks the user through defining a new custom command by voice."""
    speak("What phrase should trigger the new command?")
    trigger = listen()
    if not trigger:
        return "I didn't catch the trigger phrase, so I've cancelled that."

    speak("Should I speak a reply, or open a web page? Say 'speak' or 'open'.")
    action_word = listen() or ""
    if "open" in action_word:
        speak("What URL should I open?")
        value = listen()
        action = "open_url"
    else:
        speak("What should I say when that phrase is used?")
        value = listen()
        action = "speak"

    if not value:
        return "I didn't catch that, so I've cancelled adding the command."

    return add_custom_command(trigger, action, value)


def handle_command(raw_text: str, config: dict) -> bool:
    """
    Parse `raw_text` with the NLU layer and dispatch to the right feature.
    Returns False if the assistant should shut down, True otherwise.
    """
    # Custom (user-defined) commands take priority so they can override
    # anything built in.
    custom = match_custom_command(raw_text, config)
    if custom:
        if custom["action"] == "speak":
            speak(custom["value"])
        elif custom["action"] == "open_url":
            webbrowser.open(custom["value"])
            speak("Opening that for you.")
        return True

    intent, entities = parse_intent(raw_text)

    if intent == "exit":
        speak("Goodbye!")
        return False

    if intent == "greet":
        speak("Hello! What can I do for you?")

    elif intent == "get_time" and "date" in raw_text:
        time_str, date_str = get_time_date()
        speak(f"It's {time_str} on {date_str}.")

    elif intent == "get_time":
        time_str, _ = get_time_date()
        speak(f"It's currently {time_str}.")

    elif intent == "get_date":
        _, date_str = get_time_date()
        speak(f"Today is {date_str}.")

    elif intent == "web_search":
        speak(web_search(entities.get("query", "")))

    elif intent == "send_email":
        speak(f"Sending your email now.")
        to = entities.get("to", "")
        body = entities.get("body", "")
        result = send_email(to_address=to, subject="Voice Assistant Message", body=body)
        speak(result)

    elif intent == "set_reminder":
        result = set_reminder(
            entities.get("amount"), entities.get("unit"), entities.get("message"), speak
        )
        speak(result)

    elif intent == "get_weather":
        city = entities.get("city") or config.get("default_city", "")
        speak(get_weather(city))

    elif intent == "ask_knowledge":
        speak(ask_knowledge(entities.get("topic", "")))

    elif intent == "add_command":
        speak(handle_add_command_flow())

    else:
        speak(
            "I can chat, tell the time or date, search the web, check the "
            "weather, answer general questions, send an email, set a "
            "reminder, or learn a new custom command. What would you like?"
        )

    return True


def main() -> None:
    config = load_config()
    speak(
        "Advanced voice assistant ready. Ask me about the time, weather, "
        "a quick fact, or say 'add a command' to teach me something new."
    )

    running = True
    while running:
        command = listen()
        if command is None:
            continue
        running = handle_command(command, config)


if __name__ == "__main__":
    main()

"""
custom_commands.py
-------------------
Lets the user extend the assistant without touching code, either by:
  - editing config.json directly, or
  - saying "add a command" and being walked through it by voice.

Each custom command in config.json looks like:

    "trigger phrase": {
        "action": "speak" | "open_url",
        "value": "text to speak"  |  "https://..."
    }

At runtime, `match_custom_command` does a simple substring match: if a
saved trigger phrase appears anywhere in what the user said, that command
runs. This keeps things predictable for beginners editing the file by hand.
"""

import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {"custom_commands": {}, "default_city": ""}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def match_custom_command(text: str, config: dict) -> dict | None:
    """Return the matching command dict, or None if no trigger matches."""
    for trigger, command in config.get("custom_commands", {}).items():
        if trigger.lower() in text.lower():
            return command
    return None


def add_custom_command(trigger: str, action: str, value: str) -> str:
    """Persist a new custom command to config.json. Returns a confirmation."""
    if action not in ("speak", "open_url"):
        return "Custom commands can only 'speak' a reply or 'open_url'."

    config = load_config()
    config.setdefault("custom_commands", {})[trigger.lower().strip()] = {
        "action": action,
        "value": value,
    }
    save_config(config)
    return f"Got it. I'll remember '{trigger}' as a new command."

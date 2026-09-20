"""
reminders.py
------------
Timed reminders that fire an audible alert after a specified duration,
without blocking the main listen/respond loop.

set_reminder() schedules a threading.Timer that calls back into speak()
when it fires. Because it runs on a background thread, the assistant can
keep listening for new commands while reminders are pending.
"""

import threading

UNIT_TO_SECONDS = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
}


def set_reminder(amount: int, unit: str, message: str, speak_fn) -> str:
    """
    Schedule `speak_fn` to announce `message` after amount*unit has elapsed.
    Returns the confirmation string to speak immediately.
    """
    if not amount or not unit:
        return "Please tell me how long from now, e.g. 'in 10 minutes'."

    unit = unit.rstrip("s")  # "minutes" -> "minute"
    seconds_per_unit = UNIT_TO_SECONDS.get(unit)
    if seconds_per_unit is None:
        return f"I don't understand the time unit '{unit}'."

    delay_seconds = amount * seconds_per_unit

    def _fire():
        speak_fn(f"Reminder: {message}")

    timer = threading.Timer(delay_seconds, _fire)
    timer.daemon = True  # don't block program exit
    timer.start()

    unit_label = unit if amount == 1 else unit + "s"
    return f"Okay, I'll remind you to {message} in {amount} {unit_label}."

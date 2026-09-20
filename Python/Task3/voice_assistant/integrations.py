"""
integrations.py
----------------
Outward-facing integrations for the advanced assistant:

  - get_weather(city)     : OpenWeatherMap current-conditions lookup
  - ask_knowledge(topic)  : Wikipedia summary lookup (free, no key needed) as
                             a stand-in "QA API" / local knowledge base
  - send_email(...)       : smtplib email sending, credentials from env vars

All three fail *gracefully* and return a human-readable string rather than
raising, so a missing API key or a network hiccup never crashes the
assistant -- it just tells the user what went wrong.

Required environment variables (see .env.example / README.md):
  OPENWEATHERMAP_API_KEY
  EMAIL_ADDRESS
  EMAIL_APP_PASSWORD
  SMTP_SERVER   (defaults to smtp.gmail.com)
  SMTP_PORT     (defaults to 587)
"""

import os
import smtplib
import ssl
from email.message import EmailMessage

import requests

# Load .env if python-dotenv is available (optional convenience, not required)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

def get_weather(city: str) -> str:
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return (
            "I don't have a weather API key configured. Set the "
            "OPENWEATHERMAP_API_KEY environment variable to enable this."
        )
    if not city:
        return "Which city would you like the weather for?"

    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=6,
        )
        if resp.status_code == 404:
            return f"I couldn't find a city called {city}."
        resp.raise_for_status()
        data = resp.json()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        description = data["weather"][0]["description"]
        return (
            f"It's currently {temp:.0f} degrees Celsius in {city.title()}, "
            f"with {description}. Feels like {feels_like:.0f} degrees."
        )
    except requests.exceptions.RequestException:
        return "I couldn't reach the weather service right now."


# ---------------------------------------------------------------------------
# General knowledge Q&A (Wikipedia summary - free, keyless)
# ---------------------------------------------------------------------------

def ask_knowledge(topic: str) -> str:
    if not topic:
        return "What would you like to know about?"

    try:
        resp = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}",
            timeout=6,
            headers={"User-Agent": "voice-assistant-demo/1.0"},
        )
        if resp.status_code == 404:
            return f"I couldn't find anything about {topic}."
        resp.raise_for_status()
        data = resp.json()
        extract = data.get("extract")
        if not extract:
            return f"I couldn't find a clear answer about {topic}."
        # Keep spoken answers short.
        first_sentence = extract.split(". ")[0]
        return first_sentence if first_sentence.endswith(".") else first_sentence + "."
    except requests.exceptions.RequestException:
        return "I couldn't reach the knowledge service right now."


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def send_email(to_address: str, subject: str, body: str) -> str:
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not sender or not password:
        return (
            "Email isn't configured. Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD "
            "environment variables (use a test/dummy account and an app "
            "password, never your real account password)."
        )
    if not to_address:
        return "Who should I send the email to?"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_address
    msg["Subject"] = subject or "Voice Assistant Message"
    msg.set_content(body or "(no message content)")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls(context=context)
            server.login(sender, password)
            server.send_message(msg)
        return f"Email sent to {to_address}."
    except smtplib.SMTPAuthenticationError:
        return "Email login failed. Check your address and app password."
    except (smtplib.SMTPException, OSError):
        return "I couldn't send the email right now."

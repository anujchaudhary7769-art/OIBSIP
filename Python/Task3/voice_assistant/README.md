# Python Voice Assistant

A voice assistant built in two tiers:

- **Beginner** (`beginner_assistant.py`): voice capture, greetings, time/date,
  web search, graceful error handling, text-to-speech.
- **Advanced** (`advanced_assistant.py`): everything above, plus free-form
  NLU, email sending, timed reminders, live weather, general-knowledge Q&A,
  and user-addable custom commands.

## Project layout

```
voice_assistant/
├── core.py                # shared speak/listen/time/search helpers
├── beginner_assistant.py  # beginner-tier entry point
├── advanced_assistant.py  # advanced-tier entry point
├── nlu.py                 # rule-based intent parsing (keyword + regex)
├── integrations.py        # weather API, Wikipedia Q&A, email (smtplib)
├── reminders.py           # background-thread timed reminders
├── custom_commands.py     # load/save/match user-defined commands
├── config.json            # custom commands + default city
├── requirements.txt
├── .env.example           # template for API keys / email credentials
└── README.md
```

## Setup

1. **Install Python packages**

   ```bash
   pip install -r requirements.txt
   ```

   `PyAudio` (needed for microphone access) sometimes needs an OS-level
   dependency first:

   - **Windows**: `pip install pyaudio` usually works directly. If it fails,
     install a prebuilt wheel from
     [pypi.org/project/PyAudio](https://pypi.org/project/PyAudio/).
   - **macOS**: `brew install portaudio` then `pip install pyaudio`.
   - **Linux (Debian/Ubuntu)**: `sudo apt-get install python3-pyaudio
     portaudio19-dev` then `pip install pyaudio`.

   See the [speech_recognition PyPI page](https://pypi.org/project/SpeechRecognition/)
   for further platform notes and alternative recognizers.

2. **(Advanced tier only) Configure API keys and email**

   ```bash
   cp .env.example .env
   ```

   - Register a free API key at [openweathermap.org](https://openweathermap.org/api)
     and put it in `OPENWEATHERMAP_API_KEY`.
   - Use a **test/dummy email account** for `EMAIL_ADDRESS`. Generate an
     "app password" for it rather than using the account's real password
     (for Gmail: turn on 2-factor authentication, then create an App
     Password under Google Account → Security).
   - `.env` is loaded automatically if `python-dotenv` is installed.
     Otherwise, export the same variables in your shell before running.

3. **Run it**

   ```bash
   python beginner_assistant.py
   # or
   python advanced_assistant.py
   ```

   Say "exit", "quit", or "stop" at any time to shut down.

## Example commands

Beginner tier:
- "Hello"
- "What's the time?" / "What's the date?"
- "Search for python tutorials"

Advanced tier (free-form phrasing, not just exact keywords):
- "What's the weather like in Mumbai?"
- "Who is Alan Turing?"
- "Remind me to check the oven in 10 minutes"
- "Email test@example.com about the meeting tomorrow" *(fills the body from
  what follows "about"; edit `nlu.py`'s regex if you want richer parsing)*
- "Add a command" — then follow the voice prompts to teach a brand-new
  trigger phrase and response, saved into `config.json`

You can also hand-edit `config.json` to add custom commands directly, e.g.:

```json
"open my calendar": { "action": "open_url", "value": "https://calendar.google.com" }
```

## How the NLU works

`nlu.py` scores a spoken sentence against keyword sets per intent, then
pulls out entities (city, topic, reminder duration, email recipient, etc.)
with small regexes. It works without any extra downloads. If `nltk` is
installed and its `punkt`/`wordnet` data has been downloaded, sentences are
tokenized and lemmatized first for slightly more robust matching. For much
stronger understanding, swap `parse_intent()` for a `transformers`
zero-shot-classification pipeline or a small intent-classification model —
the rest of the assistant only depends on the `(intent, entities)` output
of that function, so the change stays contained to one file.

## Privacy: what data is processed, and how

Be aware of the following before using this assistant, especially with
real accounts:

- **Microphone audio**: `speech_recognition`'s `recognize_google()` (used
  here) sends captured audio to Google's default Web Speech API over the
  network for transcription. Audio is not stored locally by this project,
  but it does leave your machine. For fully offline/local recognition,
  swap in an offline engine such as `recognize_sphinx()` (CMU Sphinx) or
  Vosk — see the `speech_recognition` docs for alternate engines.
- **Weather queries**: the city name you speak is sent to OpenWeatherMap's
  API along with your API key.
- **Knowledge questions**: the topic you ask about is sent to Wikipedia's
  public REST API (no key, no account needed, but still a network request
  containing what you asked).
- **Email**: the recipient address and message body you dictate are sent
  to the SMTP server configured in `.env`, using the credentials for the
  test account you configured. Use a dummy/test account — never your
  primary personal email — while experimenting with this project. App
  passwords are stored only in your local `.env` file, which is not
  committed to version control (keep it in `.gitignore`).
- **Custom commands**: trigger phrases and their responses/URLs that you
  add (by voice or by hand) are stored in plain text in `config.json` on
  your machine. Don't add sensitive personal data (passwords, etc.) as a
  custom command's stored value.
- **Reminders**: reminder text is kept only in memory (a background timer)
  and is lost if the program exits before the reminder fires.

No data from this project is sent to any server other than the ones named
above (Google's speech API, OpenWeatherMap, Wikipedia, and your configured
SMTP server) — there is no analytics or telemetry.

## Extending further

- Replace the Wikipedia lookup in `integrations.py` with a different QA
  API, or point it at a local knowledge base (e.g. a JSON file of Q&A
  pairs) for fully offline general-knowledge answers.
- Add a `"smart_home"` intent in `nlu.py` and a corresponding integration
  module if you want to control smart devices (e.g. via a Home Assistant
  or SmartThings API) — follow the same "return a string, never crash"
  pattern used by `get_weather` / `ask_knowledge` / `send_email`.

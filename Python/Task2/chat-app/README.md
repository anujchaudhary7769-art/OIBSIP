# Task 5 — Chat Application

Two working programs in one repo:

- `beginner/` — a command-line chat over raw TCP sockets, one thread per client.
- `advanced/` — **Switchboard**, a browser chat app with accounts, rooms, saved history, notifications and emoji shortcodes.

Both run on localhost with no external services.

```
chat-app/
├── beginner/
│   ├── server.py
│   └── client.py
└── advanced/
    ├── app.py
    ├── emoji_map.py
    ├── requirements.txt
    ├── templates/   base.html, login.html, register.html, chat.html
    └── static/      style.css, chat.js
```

---

## Beginner tier — sockets and threading

Nothing to install. Python 3.10 or newer.

**Terminal 1 — start the server**

```bash
cd beginner
python server.py          # listens on 127.0.0.1:5050
python server.py 6000     # or pick your own port
```

**Terminals 2 and 3 — start two clients**

```bash
cd beginner
python client.py                    # connects to 127.0.0.1:5050
python client.py 127.0.0.1 6000     # or a specific host and port
```

Each client picks a display name (the server rejects duplicates), then anything you type is relayed to everyone else:

```
[14:35] Alice: Hello
[14:35] * Bob joined the chat
[14:36] Bob: hey
```

Type `/quit` or press Ctrl+C to leave. Everyone else sees `* Alice left the chat`.

### How it works

- The server binds a `SOCK_STREAM` socket and calls `accept()` in a loop. Each accepted connection gets its own daemon thread running `handle_client`.
- A `clients` dict maps name → socket, guarded by a `threading.Lock` because several threads read and mutate it.
- TCP is a byte stream, not a message stream, so both sides terminate messages with `\n` and buffer partial reads until a full line arrives. This is the part most tutorials skip, and it's why long or fast messages don't get split or glued together.
- Disconnects are handled in one place: `drop()` removes the client, closes the socket and broadcasts the departure. It runs from the `finally` block, so a clean `/quit`, a killed terminal and a network error all end up the same way.
- On the client, a background thread owns `recv()` while the main thread owns `input()`. Incoming lines are printed with `\r\033[K` first so they don't scramble the line you're halfway through typing.

---

## Advanced tier — Switchboard

```bash
cd advanced
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>, register an account, and sign in. To test with two users, open a second browser or a private window and register a different account.

`chat.db` is created automatically on first run, with `general` and `random` seeded as starting rooms.

### What's in it

| Feature | Where |
|---|---|
| Registration and login | `app.py` → `/register`, `/login`; passwords hashed with `werkzeug.security` |
| Rooms | Sidebar. Typing a new name under "Start a room" creates it |
| History | Last 50 messages of a room are sent on join (`history` event) |
| Real-time delivery | Flask-SocketIO rooms; every message is broadcast with `to=room` |
| Notifications | Browser Notification API plus an unread count in the tab title and an amber dot on the room |
| Emoji | `:fire:` → 🔥, expanded server-side in `expand_emoji()` before storage |

Around 70 shortcodes are in `emoji_map.py` — add to that dict to support more.

Clients silently `subscribe` to every room on connect so unread markers and notifications fire for rooms you aren't currently looking at; `join` is what actually opens a room, loads its history, and tells the room you've arrived.

---

## Security transparency

This is a learning project running on localhost. Be clear-eyed about what it does and doesn't protect.

**What is stored, and where**

Everything lives in a single SQLite file, `advanced/chat.db`, sitting unencrypted on disk next to the code. Anyone with read access to that file — or to a backup of it — can open it with `sqlite3 chat.db` and read all of it:

- `users` — username, password hash, account creation time.
- `rooms` — room name, creator, creation time.
- `messages` — **the full plaintext body of every message ever sent**, with its author and timestamp. Messages are never expired or deleted.

**What is not encrypted**

- **Messages are not end-to-end encrypted.** There is no client-side encryption anywhere in this app. The server reads every message in plaintext, stores it in plaintext, and can replay the entire history of any room to anyone who joins it. This is the opposite of what Signal or WhatsApp do, where the server holds only ciphertext it cannot read.
- **The database file is not encrypted at rest.**
- **Traffic is not encrypted in transit.** The dev server speaks plain HTTP and plain WebSocket (`ws://`). On localhost that's fine; over a real network anyone in the path can read every message and steal the session cookie.

**What is protected**

- Passwords are never stored in plaintext. `generate_password_hash` uses a salted PBKDF2-SHA256 hash by default, so the stored value can't be reversed into the original password.
- Sockets are rejected unless the Flask session carries a logged-in `user_id`, so an anonymous connection can't read or post.
- Message bodies are inserted into the page with `textContent`, and all SQL uses parameterised queries — so a message can't inject HTML/JavaScript or SQL.

**Before this touched a real network you'd need**, at minimum: `SECRET_KEY` from the environment rather than a hardcoded fallback, HTTPS/WSS with `session.cookie_secure`, a production server (gunicorn with an eventlet or gevent worker) instead of the Werkzeug dev server, rate limiting on login, and a real answer for message retention. End-to-end encryption would be a larger change: key exchange between clients, with the server only ever relaying ciphertext.

---

## Feature checklist

**Beginner**

- [x] Server script that listens for incoming client connections
- [x] Client script that connects to the server
- [x] Real-time, bidirectional message exchange between connected clients
- [x] Messages displayed with a timestamp prefix
- [x] Graceful disconnection handling with a notice to everyone else
- [x] Both scripts runnable on the same machine over localhost

**Advanced**

- [x] GUI served as a web app using Flask
- [x] Registration and login, username + password hash in SQLite
- [x] Multiple chat rooms, created or joined by name
- [x] Message history loaded on joining a room
- [x] In-app and desktop notification when the window isn't focused
- [x] Emoji shortcodes rendered as Unicode
- [x] README documents how messages are stored and what is not encrypted

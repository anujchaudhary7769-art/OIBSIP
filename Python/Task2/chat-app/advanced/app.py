"""Advanced tier chat server: Flask + Flask-SocketIO + SQLite.

Features: registration/login, named rooms, persisted message history,
emoji shortcodes, and presence notices.

Run:  python app.py      then open http://127.0.0.1:5000
"""

import os
import re
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import check_password_hash, generate_password_hash

from emoji_map import EMOJI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat.db")
HISTORY_LIMIT = 50

app = Flask(__name__)
# In a real deployment this must come from the environment, not a fallback.
app.config["SECRET_KEY"] = os.environ.get("CHAT_SECRET_KEY", "dev-secret-change-me")
socketio = SocketIO(app, async_mode="threading")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")
ROOMNAME_RE = re.compile(r"^[A-Za-z0-9 _-]{1,32}$")
SHORTCODE_RE = re.compile(r":([a-z0-9_+-]+):")


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rooms (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id    INTEGER NOT NULL REFERENCES rooms(id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    body       TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id, id);
"""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    now = datetime.now(timezone.utc).isoformat()
    for name in ("general", "random"):
        con.execute(
            "INSERT OR IGNORE INTO rooms (name, created_by, created_at) VALUES (?, NULL, ?)",
            (name, now),
        )
    con.commit()
    con.close()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def expand_emoji(text: str) -> str:
    """Turn :smile: into the matching Unicode character. Unknown codes stay put."""
    return SHORTCODE_RE.sub(lambda m: EMOJI.get(m.group(1), m.group(0)), text)


def local_time(iso_string: str) -> str:
    """Render a stored UTC timestamp as [HH:MM] in the server's local zone."""
    dt = datetime.fromisoformat(iso_string).astimezone()
    return dt.strftime("%H:%M")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def room_id_for(name: str, create_by: int | None = None) -> int | None:
    db = get_db()
    row = db.execute("SELECT id FROM rooms WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    if create_by is None:
        return None
    cur = db.execute(
        "INSERT INTO rooms (name, created_by, created_at) VALUES (?, ?, ?)",
        (name, create_by, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    return cur.lastrowid


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.route("/")
def index():
    return redirect(url_for("chat") if "user_id" in session else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not USERNAME_RE.match(username):
            flash("Usernames are 3-24 characters: letters, numbers, . _ or -")
        elif len(password) < 8:
            flash("Passwords need at least 8 characters.")
        else:
            db = get_db()
            taken = db.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone()
            if taken:
                flash(f"{username} is already registered. Try logging in.")
            else:
                db.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (
                        username,
                        generate_password_hash(password),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                db.commit()
                return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["user_id"] = row["id"]
            session["username"] = row["username"]
            return redirect(request.args.get("next") or url_for("chat"))
        flash("That username and password don't match an account.")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/chat")
@login_required
def chat():
    rooms = get_db().execute("SELECT name FROM rooms ORDER BY name").fetchall()
    return render_template(
        "chat.html",
        username=session["username"],
        rooms=[r["name"] for r in rooms],
    )


# --------------------------------------------------------------------------
# Socket events
# --------------------------------------------------------------------------


@socketio.on("connect")
def on_connect():
    if "user_id" not in session:
        return False  # reject unauthenticated sockets
    return None


@socketio.on("subscribe")
def on_subscribe(_data=None):
    """Silently watch every room so unread markers and notifications work.

    No history is sent and nobody is told you arrived — that only happens when
    you actually open a room with the `join` event.
    """
    if "user_id" not in session:
        return
    for row in get_db().execute("SELECT name FROM rooms"):
        join_room(row["name"])


@socketio.on("join")
def on_join(data):
    if "user_id" not in session:
        return
    name = (data or {}).get("room", "").strip()
    if not ROOMNAME_RE.match(name):
        emit("error_notice", {"message": "Room names are 1-32 characters: letters, numbers, space, _ or -"})
        return

    rid = room_id_for(name, create_by=session["user_id"])
    join_room(name)

    rows = get_db().execute(
        """SELECT m.body, m.created_at, u.username
             FROM messages m JOIN users u ON u.id = m.user_id
            WHERE m.room_id = ?
            ORDER BY m.id DESC LIMIT ?""",
        (rid, HISTORY_LIMIT),
    ).fetchall()

    emit(
        "history",
        {
            "room": name,
            "messages": [
                {
                    "user": r["username"],
                    "body": r["body"],
                    "time": local_time(r["created_at"]),
                }
                for r in reversed(rows)
            ],
        },
    )

    all_rooms = [r["name"] for r in get_db().execute("SELECT name FROM rooms ORDER BY name")]
    emit("rooms", {"rooms": all_rooms}, broadcast=True)
    emit(
        "system",
        {
            "room": name,
            "body": f"{session['username']} joined {name}",
            "time": datetime.now().strftime("%H:%M"),
        },
        to=name,
        include_self=False,
    )


@socketio.on("leave")
def on_leave(data):
    if "user_id" not in session:
        return
    name = (data or {}).get("room", "").strip()
    if not name:
        return
    leave_room(name)
    emit(
        "system",
        {
            "room": name,
            "body": f"{session['username']} left {name}",
            "time": datetime.now().strftime("%H:%M"),
        },
        to=name,
    )


@socketio.on("message")
def on_message(data):
    if "user_id" not in session:
        return
    data = data or {}
    room = data.get("room", "").strip()
    body = expand_emoji(data.get("body", "").strip())[:2000]
    if not room or not body:
        return

    rid = room_id_for(room)
    if rid is None:
        emit("error_notice", {"message": f"Room {room} no longer exists."})
        return

    now = datetime.now(timezone.utc)
    db = get_db()
    db.execute(
        "INSERT INTO messages (room_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
        (rid, session["user_id"], body, now.isoformat()),
    )
    db.commit()

    emit(
        "message",
        {
            "room": room,
            "user": session["username"],
            "body": body,
            "time": now.astimezone().strftime("%H:%M"),
        },
        to=room,
    )


if __name__ == "__main__":
    init_db()
    print("Chat running at http://127.0.0.1:5000")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True, allow_unsafe_werkzeug=True)

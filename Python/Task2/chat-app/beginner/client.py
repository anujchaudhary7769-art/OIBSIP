"""Beginner tier chat client.

Connects to the chat server, reads incoming messages on a background thread,
and sends whatever you type on the main thread.

Run:  python client.py [host] [port]
Quit: /quit  (or Ctrl+C)
"""

import socket
import sys
import threading
from datetime import datetime

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050
ENCODING = "utf-8"
BUFFER = 4096

PROMPT = "> "
running = threading.Event()
running.set()


def stamp() -> str:
    return datetime.now().strftime("[%H:%M]")


def show(line: str) -> None:
    """Print an incoming line without mangling the line being typed."""
    sys.stdout.write("\r\033[K" + line + "\n" + PROMPT)
    sys.stdout.flush()


def receive_loop(sock: socket.socket) -> None:
    buffer = ""
    try:
        while running.is_set():
            raw = sock.recv(BUFFER)
            if not raw:
                show(f"{stamp()} * Server closed the connection")
                break
            buffer += raw.decode(ENCODING, errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                if line == "BYE":
                    break
                if line == "NAME?":
                    continue  # handled during the handshake
                show(line)
    except OSError:
        if running.is_set():
            show(f"{stamp()} * Lost connection to the server")
    finally:
        running.clear()


def handshake(sock: socket.socket) -> None:
    """The server prompts with NAME? until we send an accepted name."""
    buffer = ""
    while True:
        raw = sock.recv(BUFFER)
        if not raw:
            raise ConnectionError("Server closed during the handshake")
        buffer += raw.decode(ENCODING, errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line == "NAME?":
                name = input("Choose a display name: ").strip()
                sock.sendall((name + "\n").encode(ENCODING))
            elif line:
                print(line)
                if not line.startswith("'") and "taken" not in line:
                    return  # welcome banner: we're in


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except OSError as exc:
        print(f"Could not reach {host}:{port} — {exc}")
        print("Start server.py first, then run this again.")
        return

    try:
        handshake(sock)
    except (ConnectionError, OSError) as exc:
        print(f"Handshake failed: {exc}")
        sock.close()
        return

    threading.Thread(target=receive_loop, args=(sock,), daemon=True).start()

    try:
        while running.is_set():
            text = input(PROMPT).strip()
            if not running.is_set():
                break
            if not text:
                continue
            sock.sendall((text + "\n").encode(ENCODING))
            if text == "/quit":
                break
            # Echo your own message locally; the server only relays to others.
            print(f"\033[A\r\033[K{stamp()} you: {text}")
    except (KeyboardInterrupt, EOFError):
        try:
            sock.sendall(b"/quit\n")
        except OSError:
            pass
    finally:
        running.clear()
        sock.close()
        print(f"\n{stamp()} * Disconnected")


if __name__ == "__main__":
    main()

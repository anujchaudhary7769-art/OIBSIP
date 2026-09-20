"""Beginner tier chat server.

Listens on localhost, accepts multiple clients, and relays every message to
everyone else. One thread per connected client.

Run:  python server.py [port]
"""

import socket
import sys
import threading
from datetime import datetime

HOST = "127.0.0.1"
DEFAULT_PORT = 5050
ENCODING = "utf-8"
BUFFER = 4096

# name -> socket. Guarded by clients_lock because several threads touch it.
clients: dict[str, socket.socket] = {}
clients_lock = threading.Lock()


def stamp() -> str:
    return datetime.now().strftime("[%H:%M]")


def send_line(sock: socket.socket, line: str) -> bool:
    """Send one newline-terminated line. Returns False if the peer is gone."""
    try:
        sock.sendall((line + "\n").encode(ENCODING))
        return True
    except OSError:
        return False


def broadcast(line: str, exclude: str | None = None) -> None:
    with clients_lock:
        targets = [(n, s) for n, s in clients.items() if n != exclude]
    for name, sock in targets:
        if not send_line(sock, line):
            drop(name)


def drop(name: str) -> None:
    """Remove a client and tell everyone else they left."""
    with clients_lock:
        sock = clients.pop(name, None)
    if sock is None:
        return  # already cleaned up by another thread
    try:
        sock.close()
    except OSError:
        pass
    print(f"{stamp()} * {name} disconnected")
    broadcast(f"{stamp()} * {name} left the chat")


def register(sock: socket.socket) -> str | None:
    """Ask the client for a name and make sure it is unique."""
    while True:
        send_line(sock, "NAME?")
        try:
            raw = sock.recv(BUFFER)
        except OSError:
            return None
        if not raw:
            return None
        name = raw.decode(ENCODING, errors="replace").strip()
        if not name:
            send_line(sock, "Name cannot be empty.")
            continue
        with clients_lock:
            if name in clients:
                send_line(sock, f"'{name}' is already taken. Pick another.")
                continue
            clients[name] = sock
        return name


def handle_client(sock: socket.socket, addr) -> None:
    name = register(sock)
    if name is None:
        sock.close()
        return

    print(f"{stamp()} * {name} connected from {addr[0]}:{addr[1]}")
    send_line(sock, f"{stamp()} * Welcome, {name}. Type /quit to leave.")
    with clients_lock:
        others = [n for n in clients if n != name]
    send_line(sock, f"{stamp()} * In the room: {', '.join(others) if others else 'just you'}")
    broadcast(f"{stamp()} * {name} joined the chat", exclude=name)

    buffer = ""
    try:
        while True:
            raw = sock.recv(BUFFER)
            if not raw:  # peer closed cleanly
                break
            buffer += raw.decode(ENCODING, errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                text = line.strip()
                if not text:
                    continue
                if text == "/quit":
                    send_line(sock, "BYE")
                    raise ConnectionResetError
                formatted = f"{stamp()} {name}: {text}"
                print(formatted)
                broadcast(formatted, exclude=name)
    except (ConnectionResetError, ConnectionAbortedError, OSError):
        pass  # any abrupt drop is handled the same way as a clean exit
    finally:
        drop(name)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Lets you restart the server immediately without "address already in use".
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, port))
    server.listen()
    print(f"{stamp()} Listening on {HOST}:{port} — Ctrl+C to stop")

    try:
        while True:
            sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print(f"\n{stamp()} Shutting down")
        broadcast(f"{stamp()} * Server is shutting down")
        with clients_lock:
            for sock in clients.values():
                sock.close()
            clients.clear()
    finally:
        server.close()


if __name__ == "__main__":
    main()

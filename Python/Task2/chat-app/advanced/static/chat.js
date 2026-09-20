(function () {
  "use strict";

  const shell = document.querySelector(".shell");
  const me = shell.dataset.username;

  const roomList = document.getElementById("room-list");
  const newRoomForm = document.getElementById("new-room");
  const roomNameInput = document.getElementById("room-name");
  const roomTitle = document.getElementById("room-title");
  const roomStatus = document.getElementById("room-status");
  const messages = document.getElementById("messages");
  const composer = document.getElementById("composer");
  const bodyInput = document.getElementById("body");
  const sendButton = composer.querySelector("button");

  const baseTitle = document.title;
  let activeRoom = null;
  let unreadTotal = 0;

  const socket = io();

  // ---------------------------------------------------------------- rendering

  function clearMessages() {
    messages.replaceChildren();
  }

  function addMessage(msg, opts) {
    const li = document.createElement("li");
    li.className = "msg" + (msg.user === me ? " mine" : "");

    const meta = document.createElement("div");
    meta.className = "msg-meta";

    const user = document.createElement("span");
    user.className = "msg-user";
    user.textContent = msg.user === me ? "You" : msg.user;

    const time = document.createElement("time");
    time.className = "msg-time";
    time.textContent = "[" + msg.time + "]";

    meta.append(user, time);

    const body = document.createElement("p");
    body.className = "msg-body";
    body.textContent = msg.body; // textContent, so message text can never inject HTML

    li.append(meta, body);
    messages.append(li);
    if (!opts || opts.scroll !== false) scrollToBottom();
  }

  function addSystem(text, time) {
    const li = document.createElement("li");
    li.className = "msg system";
    li.textContent = "[" + time + "] " + text;
    messages.append(li);
    scrollToBottom();
  }

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function roomButton(name) {
    return roomList.querySelector('.room[data-room="' + CSS.escape(name) + '"]');
  }

  function renderRooms(names) {
    const seen = new Set();
    names.forEach(function (name) {
      seen.add(name);
      if (roomButton(name)) return;
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.className = "room";
      button.dataset.room = name;
      button.textContent = name;
      li.append(button);
      roomList.append(li);
    });
    markActive();
  }

  function markActive() {
    roomList.querySelectorAll(".room").forEach(function (button) {
      const isActive = button.dataset.room === activeRoom;
      button.classList.toggle("active", isActive);
      if (isActive) button.classList.remove("unread");
    });
  }

  // ------------------------------------------------------------ notifications

  function askForNotifications() {
    if (!("Notification" in window)) return;
    if (Notification.permission === "default") Notification.requestPermission();
  }

  function notify(msg) {
    if (document.hasFocus() && msg.room === activeRoom) return;

    unreadTotal += 1;
    document.title = "(" + unreadTotal + ") " + baseTitle;

    const button = roomButton(msg.room);
    if (button && msg.room !== activeRoom) button.classList.add("unread");

    if ("Notification" in window && Notification.permission === "granted") {
      const note = new Notification(msg.user + " in #" + msg.room, {
        body: msg.body.slice(0, 140),
        tag: "switchboard-" + msg.room,
      });
      note.onclick = function () {
        window.focus();
        openRoom(msg.room);
        note.close();
      };
    }
  }

  window.addEventListener("focus", function () {
    unreadTotal = 0;
    document.title = baseTitle;
    if (activeRoom) markActive();
  });

  // ------------------------------------------------------------------- rooms

  function openRoom(name) {
    if (!name || name === activeRoom) return;
    activeRoom = name;
    roomTitle.textContent = name;
    roomStatus.textContent = "Loading the last messages\u2026";
    clearMessages();
    markActive();
    bodyInput.disabled = false;
    sendButton.disabled = false;
    socket.emit("join", { room: name });
    bodyInput.focus();
  }

  roomList.addEventListener("click", function (event) {
    const button = event.target.closest(".room");
    if (button) openRoom(button.dataset.room);
  });

  newRoomForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const name = roomNameInput.value.trim();
    if (!name) return;
    roomNameInput.value = "";
    openRoom(name);
  });

  composer.addEventListener("submit", function (event) {
    event.preventDefault();
    const text = bodyInput.value.trim();
    if (!text || !activeRoom) return;
    socket.emit("message", { room: activeRoom, body: text });
    bodyInput.value = "";
    askForNotifications();
  });

  // ------------------------------------------------------------ socket events

  socket.on("connect", function () {
    socket.emit("subscribe");
    const first = roomList.querySelector(".room");
    if (!activeRoom && first) {
      openRoom(first.dataset.room);
    } else if (activeRoom) {
      socket.emit("join", { room: activeRoom });
    }
  });

  socket.on("rooms", function (data) {
    renderRooms(data.rooms || []);
  });

  socket.on("history", function (data) {
    if (data.room !== activeRoom) return;
    clearMessages();
    if (!data.messages.length) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = "No messages in " + data.room + " yet. Say the first thing.";
      messages.append(li);
    } else {
      data.messages.forEach(function (msg) {
        addMessage(msg, { scroll: false });
      });
    }
    roomStatus.textContent =
      data.messages.length
        ? "Showing the last " + data.messages.length + " messages."
        : "This room is empty.";
    scrollToBottom();
  });

  socket.on("message", function (msg) {
    if (msg.room === activeRoom) {
      const empty = messages.querySelector(".empty");
      if (empty) empty.remove();
      addMessage(msg);
    }
    if (msg.user !== me) notify(msg);
  });

  socket.on("system", function (msg) {
    if (msg.room === activeRoom) addSystem(msg.body, msg.time);
  });

  socket.on("error_notice", function (data) {
    roomStatus.textContent = data.message;
  });

  socket.on("disconnect", function () {
    roomStatus.textContent = "Disconnected. Reconnecting\u2026";
    bodyInput.disabled = true;
    sendButton.disabled = true;
  });

  socket.on("connect", function () {
    bodyInput.disabled = !activeRoom;
    sendButton.disabled = !activeRoom;
  });
})();

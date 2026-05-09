from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import os
import json
import uuid
import time
from threading import Thread

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# =========================
# ORDNER
# =========================

UPLOAD_FOLDER = "uploads"
NOTES_FOLDER = "notes"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(NOTES_FOLDER, exist_ok=True)

# =========================
# DATEIEN
# =========================

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"
ANNOUNCEMENTS_FILE = "announcements.json"

# =========================
# ADMIN
# =========================

ADMIN_NAME = "admin"

# =========================
# DATEIEN ERSTELLEN
# =========================

for file_name, default in [
    (USERS_FILE, []),
    (MESSAGES_FILE, []),
    (ANNOUNCEMENTS_FILE, [])
]:
    if not os.path.exists(file_name):
        with open(file_name, "w") as f:
            json.dump(default, f)

# =========================
# HILFSFUNKTIONEN
# =========================

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# USER REGISTRIEREN
# =========================

@app.route("/register", methods=["POST"])
def register():

    data = request.json
    name = data.get("name")

    users = load_json(USERS_FILE)

    existing = False

    for user in users:
        if user["name"] == name:
            existing = True

    if not existing:

        users.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "created": time.time(),
            "notes_size": 0
        })

        save_json(USERS_FILE, users)

    return jsonify({
        "success": True
    })

# =========================
# USER LISTE
# =========================

@app.route("/users")
def users():

    return jsonify(load_json(USERS_FILE))

# =========================
# USER LÖSCHEN
# =========================

@app.route("/delete_user", methods=["POST"])
def delete_user():

    data = request.json
    user_name = data.get("user")

    users = load_json(USERS_FILE)

    new_users = []

    for user in users:

        if user["name"] != user_name:
            new_users.append(user)

    save_json(USERS_FILE, new_users)

    return jsonify({
        "success": True
    })

# =========================
# USER UMBENENNEN
# =========================

@app.route("/rename_user", methods=["POST"])
def rename_user():

    data = request.json

    old_name = data.get("old")
    new_name = data.get("new")

    users = load_json(USERS_FILE)

    for user in users:

        if user["name"] == old_name:
            user["name"] = new_name

    save_json(USERS_FILE, users)

    return jsonify({
        "success": True
    })

# =========================
# NACHRICHT SENDEN
# =========================

@app.route("/send_message", methods=["POST"])
def send_message():

    data = request.json

    messages = load_json(MESSAGES_FILE)

    messages.append({
        "id": str(uuid.uuid4()),
        "from": data.get("from"),
        "to": data.get("to"),
        "text": data.get("text"),
        "time": time.time()
    })

    save_json(MESSAGES_FILE, messages)

    return jsonify({
        "success": True
    })

# =========================
# NACHRICHTEN HOLEN
# =========================

@app.route("/messages")
def messages():

    return jsonify(load_json(MESSAGES_FILE))

# =========================
# DATEI UPLOAD
# =========================

@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:

        return jsonify({
            "success": False
        })

    file = request.files["file"]

    unique_name = str(uuid.uuid4()) + "_" + file.filename

    path = os.path.join(UPLOAD_FOLDER, unique_name)

    file.save(path)

    return jsonify({
        "success": True,
        "filename": unique_name
    })

# =========================
# ANKÜNDIGUNG SENDEN
# =========================

@app.route("/announcement", methods=["POST"])
def announcement():

    data = request.json

    announcements = load_json(ANNOUNCEMENTS_FILE)

    announcements.append({
        "id": str(uuid.uuid4()),
        "text": data.get("text"),
        "time": time.time()
    })

    save_json(ANNOUNCEMENTS_FILE, announcements)

    return jsonify({
        "success": True
    })

# =========================
# ANKÜNDIGUNGEN HOLEN
# =========================

@app.route("/announcements")
def announcements():

    return jsonify(load_json(ANNOUNCEMENTS_FILE))

# =========================
# NOTIZEN SPEICHERN
# =========================

@app.route("/save_notes", methods=["POST"])
def save_notes():

    data = request.json

    user = data.get("user")
    text = data.get("text")

    # 2 MB LIMIT
    if len(text.encode("utf-8")) > 2 * 1024 * 1024:

        return jsonify({
            "success": False,
            "error": "2MB überschritten"
        })

    note_path = os.path.join(
        NOTES_FOLDER,
        f"{user}.txt"
    )

    with open(note_path, "w", encoding="utf-8") as f:
        f.write(text)

    return jsonify({
        "success": True
    })

# =========================
# NOTIZEN HOLEN
# =========================

@app.route("/load_notes/<user>")
def load_notes(user):

    note_path = os.path.join(
        NOTES_FOLDER,
        f"{user}.txt"
    )

    if not os.path.exists(note_path):

        return jsonify({
            "text": ""
        })

    with open(note_path, "r", encoding="utf-8") as f:

        text = f.read()

    return jsonify({
        "text": text
    })

# =========================
# VERSTECKEN SPIEL
# =========================

players = []

@socketio.on("join_hide_game")
def join_hide_game(data):

    players.append(data["player"])

    emit(
        "player_count",
        {
            "count": len(players),
            "players": players
        },
        broadcast=True
    )

@socketio.on("start_hide_game")
def start_hide_game():

    if len(players) >= 2:

        seeker = players[0]

        emit(
            "hide_game_started",
            {
                "seeker": seeker
            },
            broadcast=True
        )

# =========================
# SPIELER BEWEGEN
# =========================

@socketio.on("move")
def move(data):

    emit(
        "player_moved",
        data,
        broadcast=True
    )

# =========================
# TIC TAC TOE
# =========================

ttt_board = [""] * 9
ttt_turn = "X"

@socketio.on("ttt_move")
def ttt_move(data):

    global ttt_turn

    index = data["index"]

    if ttt_board[index] == "":

        ttt_board[index] = ttt_turn

        emit(
            "ttt_update",
            {
                "board": ttt_board,
                "turn": ttt_turn
            },
            broadcast=True
        )

        if ttt_turn == "X":
            ttt_turn = "O"
        else:
            ttt_turn = "X"

# =========================
# PING PONG
# =========================

pong_data = {
    "ball_x": 100,
    "ball_y": 100,
    "speed_x": 5,
    "speed_y": 5
}

@socketio.on("pong_update")
def pong_update(data):

    global pong_data

    pong_data = data

    emit(
        "pong_state",
        pong_data,
        broadcast=True
    )

# =========================
# DATEIEN + NACHRICHTEN LÖSCHEN
# =========================

def cleanup_loop():

    while True:

        now = time.time()

        # DATEIEN NACH 1H LÖSCHEN

        for file in os.listdir(UPLOAD_FOLDER):

            path = os.path.join(
                UPLOAD_FOLDER,
                file
            )

            if os.path.isfile(path):

                age = now - os.path.getmtime(path)

                if age > 3600:
                    os.remove(path)

        # NACHRICHTEN NACH 20 TAGEN LÖSCHEN

        messages = load_json(MESSAGES_FILE)

        new_messages = []

        for msg in messages:

            age = now - msg["time"]

            if age < 20 * 24 * 60 * 60:
                new_messages.append(msg)

        save_json(
            MESSAGES_FILE,
            new_messages
        )

        time.sleep(60)

# =========================
# CLEANUP THREAD START
# =========================

Thread(
    target=cleanup_loop,
    daemon=True
).start()

# =========================
# SERVER START
# =========================

if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000
    )

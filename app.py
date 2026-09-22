import json
import os
import random

from flask import Flask, jsonify, render_template, request, session


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

TOTAL_ROOMS = 15
PLAYER_MAX_HP = 5

QUESTION_FILES = {
    "EASY": "questions.json",
    "MEDIUM": "questions_medium.json",
    "HARD": "questions_hard.json",
}

NORMAL_ENEMIES = {
    "EASY": [
        {"name": "Spam Bot", "icon": "🤖"},
        {"name": "Phishing Email", "icon": "📧"},
        {"name": "Adware Bug", "icon": "🐛"},
    ],
    "MEDIUM": [
        {"name": "Botnet Node", "icon": "🧟"},
        {"name": "Credential Thief", "icon": "🔓"},
        {"name": "Malware Loader", "icon": "👾"},
    ],
    "HARD": [
        {"name": "Ransomware", "icon": "💀"},
        {"name": "Insider Threat", "icon": "🕵️"},
        {"name": "Zero-Day Exploit", "icon": "🐉"},
    ],
}

BOSSES = {
    5: {
        "name": "Phishing King",
        "icon": "🎣",
        "kind": "MINIBOSS",
        "max_hp": 3,
        "attack": 1,
    },
    10: {
        "name": "Ransomware Overlord",
        "icon": "🦠",
        "kind": "MAJOR BOSS",
        "max_hp": 4,
        "attack": 1,
    },
    15: {
        "name": "The Root Admin",
        "icon": "👑",
        "kind": "FINAL BOSS",
        "max_hp": 5,
        "attack": 2,
    },
}


def load_questions(tier=None):
    """Load one difficulty bank, or combine all banks when no tier is given."""
    if tier:
        with open(QUESTION_FILES[tier], "r", encoding="utf-8") as file:
            return json.load(file)

    questions = []
    for difficulty in QUESTION_FILES:
        questions.extend(load_questions(difficulty))
    return questions


def get_tier(room):
    if room <= 5:
        return "EASY"
    if room <= 10:
        return "MEDIUM"
    return "HARD"


def create_enemy(room):
    """Create the enemy for a room. Rooms 5, 10 and 15 are boss rooms."""
    if room in BOSSES:
        enemy = BOSSES[room].copy()
    else:
        template = random.choice(NORMAL_ENEMIES[get_tier(room)])
        enemy = {
            **template,
            "kind": "ENEMY",
            "max_hp": 1,
            "attack": 1,
        }

    enemy["hp"] = enemy["max_hp"]
    return enemy


def public_stats(state):
    """Return only the game information that is safe for the browser to see."""
    return {
        "room": state["current_room"],
        "total_rooms": TOTAL_ROOMS,
        "hp": state["hp"],
        "max_hp": state["max_hp"],
        "credits": state["credits"],
        "combo": state["combo"],
        "enemy": state.get("enemy"),
    }


def current_question(state):
    tier = get_tier(state["current_room"])
    questions = load_questions(tier)
    order = state["question_orders"][tier]
    question_number = state["question_positions"][tier]

    if question_number >= len(order):
        # This is rare, but reshuffling prevents a long run from crashing.
        new_order = list(range(len(questions)))
        random.shuffle(new_order)
        order.extend(new_order)

    return questions[order[question_number]]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_game():
    question_orders = {}
    for tier in QUESTION_FILES:
        question_order = list(range(len(load_questions(tier))))
        random.shuffle(question_order)
        question_orders[tier] = question_order

    session["game_state"] = {
        "question_orders": question_orders,
        "question_positions": {tier: 0 for tier in QUESTION_FILES},
        "current_room": 1,
        "hp": PLAYER_MAX_HP,
        "max_hp": PLAYER_MAX_HP,
        "credits": 0,
        "combo": 0,
        "packet_sniffer_used": False,
        "enemy": create_enemy(1),
        "game_over": False,
    }

    return jsonify({"status": "started", **public_stats(session["game_state"])})


@app.route("/api/question", methods=["GET"])
def get_question():
    state = session.get("game_state")
    if not state or state.get("game_over"):
        return jsonify({"error": "No active run"}), 400

    question = current_question(state)
    tier = get_tier(state["current_room"])
    return jsonify({
        "tier": tier,
        "domain": question.get("domain", "General Security"),
        "question": question["question"],
        "options": question["options"],
        "packet_sniffer_available": not state["packet_sniffer_used"],
        **public_stats(state),
    })


@app.route("/api/answer", methods=["POST"])
def submit_answer():
    state = session.get("game_state")
    if not state or state.get("game_over"):
        return jsonify({"error": "No active run"}), 400

    data = request.get_json() or {}
    user_answer = data.get("answer")
    is_timeout = data.get("timeout", False)
    question = current_question(state)
    correct_answer = question.get("answer") or question.get("correct")
    tier = get_tier(state["current_room"])
    state["question_positions"][tier] += 1

    if is_timeout or user_answer != correct_answer:
        damage_taken = state["enemy"]["attack"]
        state["hp"] = max(0, state["hp"] - damage_taken)
        state["combo"] = 0

        if state["hp"] == 0:
            state["game_over"] = True
            status = "game_over"
        else:
            status = "player_hit"

        session.modified = True
        return jsonify({
            "status": status,
            "was_timeout": is_timeout,
            "correct_answer": correct_answer,
            "explanation": question.get("explanation", ""),
            "damage_taken": damage_taken,
            **public_stats(state),
        })

    state["combo"] += 1
    damage_dealt = 2 if state["combo"] % 3 == 0 else 1
    state["enemy"]["hp"] = max(0, state["enemy"]["hp"] - damage_dealt)
    credits_earned = 10 + (state["combo"] * 2)
    state["credits"] += credits_earned

    enemy_defeated = state["enemy"]["hp"] == 0
    defeated_enemy = state["enemy"]["name"] if enemy_defeated else None

    if enemy_defeated:
        if state["current_room"] == TOTAL_ROOMS:
            state["game_over"] = True
            status = "won"
        else:
            state["current_room"] += 1
            state["enemy"] = create_enemy(state["current_room"])
            status = "room_cleared"
    else:
        status = "enemy_hit"

    session.modified = True
    return jsonify({
        "status": status,
        "correct_answer": correct_answer,
        "explanation": question.get("explanation", ""),
        "damage_dealt": damage_dealt,
        "credits_earned": credits_earned,
        "defeated_enemy": defeated_enemy,
        **public_stats(state),
    })


@app.route("/api/powerup/packet-sniffer", methods=["POST"])
def use_packet_sniffer():
    state = session.get("game_state")
    if not state or state.get("game_over"):
        return jsonify({"error": "No active run"}), 400

    if state["packet_sniffer_used"]:
        return jsonify({"error": "Packet Sniffer already used"}), 400

    question = current_question(state)
    correct_answer = question.get("answer") or question.get("correct")
    incorrect_keys = [key for key in question["options"] if key != correct_answer]
    removed_keys = random.sample(incorrect_keys, 2)

    state["packet_sniffer_used"] = True
    session.modified = True
    return jsonify({"status": "success", "removed": removed_keys})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

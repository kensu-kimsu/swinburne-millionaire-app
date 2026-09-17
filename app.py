import json
import random
from flask import Flask, jsonify, render_template, request, session

app = Flask(__name__)
app.secret_key = "swinburne_millionaire_secret_key"

PRIZES = [
    "$100", "$200", "$300", "$500", "$1,000",
    "$2,000", "$4,000", "$8,000", "$16,000", "$32,000",
    "$64,000", "$125,000", "$250,000", "$500,000", "$1,000,000"
]

WRONG_ANSWER_INSULTS = [
    "Even a random guesser had a 25% chance, yet here we are.",
    "Is that your final answer, or just your final mistake?",
    "That answer was so wrong, your degree just un-enrolled itself.",
    "Congratulations! You've successfully managed to walk away with nothing.",
    "Don't worry, poverty builds character!",
    "Errors like that are why firewalls were invented in the first place."
]

TIMEOUT_INSULTS = [
    "Did you fall asleep at the keyboard?",
    "30 seconds wasn't enough? Were you reading with your fingers?",
    "Time flies when you're staring blankly at the screen!",
    "The timer reached zero faster than your brain cells could connect.",
    "You hesitated so long even the server almost went to sleep.",
    "Clocked out early? Next time, try answering before retirement!"
]

def load_questions():
    try:
        with open("questions_2.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        with open("questions.json", "r", encoding="utf-8") as f:
            return json.load(f)

def get_tier(step):
    if step < 5:
        return "EASY"
    elif step < 10:
        return "MEDIUM"
    return "HARD"

def get_guaranteed_prize(step):
    if step > 9:
        return "$32,000"
    elif step > 4:
        return "$1,000"
    return "$0"

@app.route("/")
def index():
    return render_template(
        "index.html",
        title="Swinburne Millionaire",
        subtitle="Are you smart enough to win $1,000,000?",
    )

@app.route("/api/start", methods=["POST"])
def start_game():
    questions = load_questions()

    if len(questions) < 15:
        selected_questions = random.choices(questions, k=15)
    else:
        selected_questions = random.sample(questions, 15)

    session["game_state"] = {
        "questions": selected_questions,
        "current_step": 0,
        "lifeline_5050_used": False,
        "game_over": False,
        "walked_away": False,
    }

    return jsonify({"status": "started", "total_questions": 15})

@app.route("/api/question", methods=["GET"])
def get_question():
    state = session.get("game_state")
    if not state or state.get("game_over"):
        return jsonify({"error": "No active game"}), 400

    step = state["current_step"]
    if step >= len(state["questions"]):
        return jsonify({"status": "completed"})

    q = state["questions"][step]

    return jsonify({
        "step": step,
        "prize": PRIZES[step],
        "tier": get_tier(step),
        "domain": q.get("domain", "General Security"),
        "question": q["question"],
        "options": q["options"],
        "lifeline_5050_available": not state["lifeline_5050_used"],
        "walked_away": state.get("walked_away", False),
    })

@app.route("/api/answer", methods=["POST"])
def submit_answer():
    state = session.get("game_state")
    if not state or state.get("game_over"):
        return jsonify({"error": "No active game"}), 400

    data = request.get_json() or {}
    user_answer = data.get("answer")
    is_timeout = data.get("timeout", False)

    step = state["current_step"]
    q = state["questions"][step]
    correct_answer = q.get("answer") or q.get("correct")

    if state.get("walked_away"):
        state["game_over"] = True
        session.modified = True
        return jsonify({
            "status": "walked_away_revealed",
            "user_choice": user_answer,
            "correct_answer": correct_answer,
            "is_correct": (user_answer == correct_answer),
            "explanation": q.get("explanation", ""),
            "prize_won": PRIZES[step - 1] if step > 0 else "$0",
        })

    if is_timeout:
        state["game_over"] = True
        session.modified = True
        return jsonify({
            "status": "timeout",
            "correct_answer": correct_answer,
            "explanation": q.get("explanation", ""),
            "prize_won": get_guaranteed_prize(step),
            "insult": random.choice(TIMEOUT_INSULTS)
        })

    if user_answer != correct_answer:
        state["game_over"] = True
        session.modified = True
        return jsonify({
            "status": "wrong",
            "correct_answer": correct_answer,
            "explanation": q.get("explanation", ""),
            "prize_won": get_guaranteed_prize(step),
            "insult": random.choice(WRONG_ANSWER_INSULTS)
        })

    state["current_step"] += 1
    next_step = state["current_step"]

    if next_step >= 15:
        state["game_over"] = True
        session.modified = True
        return jsonify({
            "status": "won",
            "correct_answer": correct_answer,
            "explanation": q.get("explanation", ""),
            "prize_won": "$1,000,000",
        })

    checkpoint_reached = next_step in [5, 10]
    guaranteed_prize = get_guaranteed_prize(next_step)

    session.modified = True

    return jsonify({
        "status": "correct",
        "correct_answer": correct_answer,
        "explanation": q.get("explanation", ""),
        "checkpoint_reached": checkpoint_reached,
        "guaranteed_prize": guaranteed_prize,
        "next_step": next_step,
    })

@app.route("/api/cashout", methods=["POST"])
def cashout():
    state = session.get("game_state")
    if not state or state.get("game_over"):
        return jsonify({"error": "No active game"}), 400

    step = state["current_step"]
    state["walked_away"] = True
    session.modified = True

    prize_won = PRIZES[step - 1] if step > 0 else "$0"
    return jsonify({
        "status": "walk_away_initiated",
        "prize_won": prize_won,
        "message": "You walked away! Take a guess to see if you would have been correct.",
    })

@app.route("/api/checkpoint_choice", methods=["POST"])
def checkpoint_choice():
    data = request.get_json() or {}
    user_choice = data.get("choice")

    state = session.get("game_state")
    if not state or state.get("game_over"):
        return jsonify({"error": "No active game"}), 400

    if user_choice == "cashout":
        step = state["current_step"]
        prize_won = get_guaranteed_prize(step)
        state["walked_away"] = True
        state["game_over"] = True
        session.modified = True
        return jsonify({"status": "cashed_out", "prize_won": prize_won})

    return jsonify({"status": "continue"})

@app.route("/api/lifeline/5050", methods=["POST"])
def lifeline_5050():
    state = session.get("game_state")
    if not state or state.get("game_over"):
        return jsonify({"error": "No active game"}), 400

    if state["lifeline_5050_used"]:
        return jsonify({"error": "Lifeline already used"}), 400

    step = state["current_step"]
    q = state["questions"][step]
    correct_answer = q.get("answer") or q.get("correct")

    incorrect_keys = [k for k in q["options"].keys() if k != correct_answer]
    removed_keys = random.sample(incorrect_keys, 2)

    state["lifeline_5050_used"] = True
    session.modified = True

    return jsonify({"status": "success", "removed": removed_keys})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
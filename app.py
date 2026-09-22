import json
import os
import random

from flask import Flask, has_request_context, jsonify, render_template, request, session


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

TOTAL_ROOMS = 15
INVENTORY_LIMIT = 4
PLAYER_MAX_HP = 5

QUESTION_FILES = {
    "EASY": "questions.json",
    "MEDIUM": "questions_medium.json",
    "HARD": "questions_hard.json",
}

ITEMS = {
    "packet_sniffer": {
        "name": "Packet Sniffer", "icon": "🔍", "rarity": "Common", "price": 75,
        "description": "Remove two incorrect answers from the current question.",
    },
    "firewall": {
        "name": "Firewall", "icon": "🛡️", "rarity": "Common", "price": 90,
        "description": "Block the next enemy attack.",
    },
    "health_patch": {
        "name": "Health Patch", "icon": "❤️‍🩹", "rarity": "Common", "price": 80,
        "description": "Restore 2 HP, up to your maximum HP.",
    },
    "overclock": {
        "name": "Overclock", "icon": "⏱️", "rarity": "Uncommon", "price": 100,
        "description": "Add 15 seconds to the current question.",
    },
    "sandbox": {
        "name": "Sandbox", "icon": "🧪", "rarity": "Uncommon", "price": 110,
        "description": "The next wrong answer causes no HP damage.",
    },
    "zero_day": {
        "name": "Zero-Day", "icon": "💉", "rarity": "Rare", "price": 150,
        "description": "Immediately deal 2 damage to the current enemy.",
    },
    "backup": {
        "name": "Backup", "icon": "💾", "rarity": "Rare", "price": 170,
        "description": "Automatically revive with 1 HP after fatal damage.",
    },
}

RELICS = {
    "exploit_chain": {
        "name": "Exploit Chain", "icon": "🔥",
        "description": "Every third correct answer deals 3 damage instead of 2.",
    },
    "tux_kernel": {
        "name": "Tux Kernel", "icon": "🐧",
        "description": "Correct Linux answers deal +1 damage.",
    },
    "wireshark": {
        "name": "Wireshark", "icon": "🦈",
        "description": "Networking questions receive 5 extra seconds.",
    },
    "web_proxy": {
        "name": "Web Proxy", "icon": "🌐",
        "description": "Correct Web Security answers deal +1 damage.",
    },
    "zero_trust": {
        "name": "Zero Trust", "icon": "🧱",
        "description": "Every fifth incoming enemy attack is blocked.",
    },
    "root_access": {
        "name": "Root Access", "icon": "🔑",
        "description": "Bosses begin combat with 1 HP already removed.",
    },
    "incident_response": {
        "name": "Incident Response Plan", "icon": "🚑",
        "description": "Restore 1 HP after defeating a boss.",
    },
    "credit_miner": {
        "name": "Credit Miner", "icon": "🪙",
        "description": "Earn 5 additional credits for every correct answer.",
    },
}

ABILITIES = {
    "shielded": {
        "name": "Hardened Shell", "icon": "🛡️",
        "description": "The first successful attack against this enemy deals 1 less damage.",
    },
    "haste": {
        "name": "Time Compression", "icon": "⏳",
        "description": "Questions begin with only 20 seconds.",
    },
    "jammer": {
        "name": "Signal Jammer", "icon": "📵",
        "description": "Packet Sniffer cannot be used during this battle.",
    },
    "leech": {
        "name": "Data Leech", "icon": "🩸",
        "description": "The enemy restores 1 HP after each wrong answer.",
    },
    "credit_drain": {
        "name": "Wallet Drain", "icon": "💸",
        "description": "A wrong answer also removes 20 credits.",
    },
    "encryptor": {
        "name": "Encryption", "icon": "🔒",
        "description": "A wrong answer destroys one random inventory item.",
    },
    "regenerate": {
        "name": "Self Repair", "icon": "♻️",
        "description": "The enemy restores 1 HP after each wrong answer.",
    },
    "brutal": {
        "name": "Critical Strike", "icon": "💥",
        "description": "Enemy attacks deal 1 additional HP damage.",
    },
}

NORMAL_ENEMIES = {
    "EASY": [
        {"id": "spam_bot", "name": "Spam Bot", "icon": "🤖", "abilities": ["credit_drain"]},
        {"id": "phishing_email", "name": "Phishing Email", "icon": "📧", "abilities": ["jammer"]},
        {"id": "adware_bug", "name": "Adware Bug", "icon": "🐛", "abilities": ["leech"]},
    ],
    "MEDIUM": [
        {"id": "botnet_node", "name": "Botnet Node", "icon": "🧟", "abilities": ["shielded"]},
        {"id": "credential_thief", "name": "Credential Thief", "icon": "🔓", "abilities": ["credit_drain"]},
        {"id": "malware_loader", "name": "Malware Loader", "icon": "👾", "abilities": ["haste"]},
    ],
    "HARD": [
        {"id": "ransomware", "name": "Ransomware", "icon": "💀", "abilities": ["encryptor"]},
        {"id": "insider_threat", "name": "Insider Threat", "icon": "🕵️", "abilities": ["brutal"]},
        {"id": "zero_day_exploit", "name": "Zero-Day Exploit", "icon": "🐉", "abilities": ["regenerate"]},
    ],
}

BOSSES = {
    5: {
        "id": "phishing_king", "name": "Phishing King", "icon": "🎣",
        "kind": "MINIBOSS", "max_hp": 4, "attack": 1, "abilities": ["jammer"],
    },
    10: {
        "id": "ransomware_overlord", "name": "Ransomware Overlord", "icon": "🦠",
        "kind": "MAJOR BOSS", "max_hp": 6, "attack": 1, "abilities": ["encryptor", "shielded"],
    },
    15: {
        "id": "root_admin", "name": "The Root Admin", "icon": "👑",
        "kind": "FINAL BOSS", "max_hp": 8, "attack": 2,
        "abilities": ["haste", "regenerate"],
    },
}

ROOMS = {
    "combat": {"name": "Combat", "icon": "⚔️", "description": "Fight a normal enemy."},
    "elite": {"name": "Elite", "icon": "💀", "description": "Fight a stronger enemy for improved rewards."},
    "loot": {"name": "Data Cache", "icon": "🎁", "description": "Choose a free consumable or credits."},
    "heal": {"name": "Repair Station", "icon": "❤️", "description": "Restore HP or improve maximum HP."},
    "shop": {"name": "Dark Web Market", "icon": "🛒", "description": "Spend credits on consumables."},
    "event": {"name": "Unknown Signal", "icon": "❓", "description": "Make a risky decision with an uncertain outcome."},
    "boss": {"name": "Boss", "icon": "👑", "description": "A powerful enemy with special abilities."},
}

MECHANICS = {
    "combat": {"name": "Quiz Combat", "description": "Correct answers damage enemies. Wrong answers allow enemies to attack."},
    "combo": {"name": "Combo Damage", "description": "Every third consecutive correct answer deals additional damage."},
    "routes": {"name": "Route Choices", "description": "Choose between two rooms to shape the current run."},
    "inventory": {"name": "Inventory", "description": "Carry up to four consumable items and choose when to use them."},
    "loot": {"name": "Loot", "description": "Defeated enemies and data caches offer a choice of rewards."},
    "relics": {"name": "Relics", "description": "Relics provide passive bonuses that last for the entire run."},
    "shops": {"name": "Shops", "description": "Credits earned in combat can purchase useful consumables."},
    "events": {"name": "Random Events", "description": "Events offer choices that can produce rewards or penalties."},
    "elites": {"name": "Elite Enemies", "description": "Elites have more HP and abilities but provide stronger rewards."},
    "bosses": {"name": "Boss Battles", "description": "Bosses have multiple HP, stronger attacks, and unique abilities."},
    "progression": {"name": "Discovery Progress", "description": "Enemies, items, relics, rooms, and abilities appear in the encyclopedia after discovery."},
}

EVENTS = {
    "suspicious_usb": {
        "name": "Suspicious USB", "icon": "💾",
        "text": "An unknown USB drive is connected to an abandoned workstation.",
        "choices": [
            {"id": "scan", "label": "Scan it safely", "description": "Gain a smaller guaranteed reward."},
            {"id": "insert", "label": "Open it directly", "description": "Risk HP for a chance at valuable loot."},
        ],
    },
    "open_wifi": {
        "name": "Open Wi-Fi", "icon": "📡",
        "text": "An unsecured wireless network is broadcasting nearby.",
        "choices": [
            {"id": "monitor", "label": "Monitor traffic", "description": "Gain credits without connecting."},
            {"id": "connect", "label": "Connect to it", "description": "Find an item or suffer an attack."},
        ],
    },
    "leaked_database": {
        "name": "Leaked Database", "icon": "🗄️",
        "text": "A database of exposed credentials appears on a hidden service.",
        "choices": [
            {"id": "report", "label": "Report the leak", "description": "Restore HP for responsible disclosure."},
            {"id": "sell", "label": "Sell the data", "description": "Gain many credits but lose HP."},
        ],
    },
    "legacy_server": {
        "name": "Legacy Server", "icon": "🖥️",
        "text": "A forgotten server is still running an unsupported operating system.",
        "choices": [
            {"id": "patch", "label": "Patch the server", "description": "Spend credits to restore HP."},
            {"id": "exploit", "label": "Exploit the server", "description": "Risk damage for a rare item."},
        ],
    },
}


def load_questions(tier=None):
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


def default_progress():
    return {
        "runs_started": 0,
        "runs_completed": 0,
        "best_room": 0,
        "unlocked_items": ["packet_sniffer"],
        "unlocked_relics": [],
        "unlocked_enemies": [],
        "unlocked_abilities": [],
        "unlocked_rooms": ["combat"],
        "unlocked_mechanics": ["combat", "combo", "routes", "progression"],
    }


def get_progress():
    if "meta_progress" not in session:
        session["meta_progress"] = default_progress()
    return session["meta_progress"]


def discover(category, entry_id):
    if not has_request_context():
        return
    progress = get_progress()
    key = f"unlocked_{category}"
    if entry_id not in progress[key]:
        progress[key].append(entry_id)
        session.modified = True


def record_room(room):
    progress = get_progress()
    if room > progress["best_room"]:
        progress["best_room"] = room
        session.modified = True


def item_view(item_id):
    return {"id": item_id, **ITEMS[item_id]}


def relic_view(relic_id):
    return {"id": relic_id, **RELICS[relic_id]}


def ability_view(ability_id):
    return {"id": ability_id, **ABILITIES[ability_id]}


def room_view(room_id):
    return {"id": room_id, **ROOMS[room_id]}


def create_enemy(room, elite=False, relics=None):
    if room in BOSSES and not elite:
        enemy = BOSSES[room].copy()
    else:
        template = random.choice(NORMAL_ENEMIES[get_tier(room)])
        enemy = {
            **template,
            "kind": "ELITE" if elite else "ENEMY",
            "max_hp": 3 if elite else 1,
            "attack": 1,
        }
        if elite:
            extra = random.choice([ability for ability in ABILITIES if ability not in enemy["abilities"]])
            enemy["abilities"] = [*enemy["abilities"], extra]

    enemy["hp"] = enemy["max_hp"]
    enemy["armor"] = 1 if "shielded" in enemy["abilities"] else 0
    if "root_access" in (relics or []) and enemy["kind"] != "ENEMY":
        enemy["hp"] = max(1, enemy["hp"] - 1)

    discover("enemies", enemy["id"])
    for ability in enemy["abilities"]:
        discover("abilities", ability)
    return enemy


def shuffled_question_orders():
    orders = {}
    for tier in QUESTION_FILES:
        order = list(range(len(load_questions(tier))))
        random.shuffle(order)
        orders[tier] = order
    return orders


def current_question(state):
    tier = get_tier(state["current_room"])
    questions = load_questions(tier)
    order = state["question_orders"][tier]
    position = state["question_positions"][tier]
    if position >= len(order):
        new_order = list(range(len(questions)))
        random.shuffle(new_order)
        order.extend(new_order)
    return questions[order[position]]


def public_enemy(enemy):
    if not enemy:
        return None
    return {
        **enemy,
        "ability_details": [ability_view(ability) for ability in enemy["abilities"]],
    }


def public_state(state):
    return {
        "room": state["current_room"],
        "total_rooms": TOTAL_ROOMS,
        "hp": state["hp"],
        "max_hp": state["max_hp"],
        "credits": state["credits"],
        "combo": state["combo"],
        "inventory_limit": INVENTORY_LIMIT,
        "inventory": [item_view(item) for item in state["inventory"]],
        "relics": [relic_view(relic) for relic in state["relics"]],
        "effects": state["effects"],
        "enemy": public_enemy(state.get("enemy")),
        "pending": state.get("pending"),
        "room_options": [room_view(room) for room in state.get("room_options", [])],
        "reward_kind": state.get("reward_kind"),
        "reward_options": state.get("reward_options", []),
        "shop_items": state.get("shop_items", []),
        "event": state.get("event"),
        "stats": state["stats"],
        "game_over": state["game_over"],
        "won": state.get("won", False),
    }


def choose_item_rewards(count=2):
    item_ids = random.sample(list(ITEMS), count)
    for item_id in item_ids:
        discover("items", item_id)
    rewards = [{"type": "item", **item_view(item_id)} for item_id in item_ids]
    rewards.append({
        "type": "credits", "id": "credits_50", "name": "Credit Cache",
        "icon": "🪙", "rarity": "Common", "description": "Gain 50 credits.",
    })
    return rewards


def choose_relic_rewards():
    relic_ids = random.sample(list(RELICS), 3)
    for relic_id in relic_ids:
        discover("relics", relic_id)
    return [{"type": "relic", **relic_view(relic_id)} for relic_id in relic_ids]


def set_reward(state, kind):
    state["pending"] = "reward"
    state["reward_kind"] = kind
    state["reward_options"] = choose_relic_rewards() if kind == "relic" else choose_item_rewards()
    discover("mechanics", "loot")


def generate_room_options():
    available = ["combat", "elite", "loot", "heal", "shop", "event"]
    choices = random.sample(available, 2)
    for room_type in choices:
        discover("rooms", room_type)
    return choices


def advance_stage(state):
    state["current_room"] += 1
    record_room(state["current_room"])
    state["enemy"] = None
    state["pending"] = None
    state["reward_options"] = []
    state["shop_items"] = []
    state["event"] = None
    if state["current_room"] in BOSSES:
        state["enemy"] = create_enemy(state["current_room"], relics=state["relics"])
        discover("rooms", "boss")
        discover("mechanics", "bosses")
    else:
        state["pending"] = "route"
        state["room_options"] = generate_room_options()


def build_shop():
    choices = random.sample(list(ITEMS), 3)
    for item_id in choices:
        discover("items", item_id)
    return [{**item_view(item_id), "type": "item"} for item_id in choices]


def start_room(state, room_type):
    state["pending"] = None
    state["room_options"] = []
    state["enemy"] = None
    discover("rooms", room_type)
    if room_type == "combat":
        state["enemy"] = create_enemy(state["current_room"], relics=state["relics"])
    elif room_type == "elite":
        state["enemy"] = create_enemy(state["current_room"], elite=True, relics=state["relics"])
        discover("mechanics", "elites")
    elif room_type == "loot":
        set_reward(state, "item")
    elif room_type == "heal":
        state["pending"] = "heal"
    elif room_type == "shop":
        state["pending"] = "shop"
        state["shop_items"] = build_shop()
        discover("mechanics", "shops")
    elif room_type == "event":
        state["pending"] = "event"
        event_id = random.choice(list(EVENTS))
        state["event"] = {"id": event_id, **EVENTS[event_id]}
        discover("mechanics", "events")


def remove_random_item(state):
    if not state["inventory"]:
        return None
    index = random.randrange(len(state["inventory"]))
    return state["inventory"].pop(index)


def complete_combat(state):
    enemy = state["enemy"]
    state["stats"]["enemies_defeated"] += 1
    state["enemy"] = None
    if state["current_room"] == TOTAL_ROOMS:
        state["game_over"] = True
        state["won"] = True
        state["pending"] = "complete"
        progress = get_progress()
        progress["runs_completed"] += 1
        record_room(TOTAL_ROOMS)
        return "won"

    if enemy["kind"] in {"MINIBOSS", "MAJOR BOSS"}:
        if "incident_response" in state["relics"]:
            state["hp"] = min(state["max_hp"], state["hp"] + 1)
        set_reward(state, "relic")
    elif enemy["kind"] == "ELITE":
        if random.random() < 0.4:
            set_reward(state, "relic")
        else:
            set_reward(state, "item")
    else:
        set_reward(state, "item")
    return "enemy_defeated"


def finish_failed_run(state):
    state["game_over"] = True
    state["pending"] = "complete"
    record_room(state["current_room"])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_game():
    progress = get_progress()
    progress["runs_started"] += 1
    bonus_hp = 1 if progress["runs_completed"] >= 1 else 0
    starting_credits = 50 if progress["runs_started"] >= 3 else 0
    session["game_state"] = {
        "question_orders": shuffled_question_orders(),
        "question_positions": {tier: 0 for tier in QUESTION_FILES},
        "current_room": 1,
        "hp": PLAYER_MAX_HP + bonus_hp,
        "max_hp": PLAYER_MAX_HP + bonus_hp,
        "credits": starting_credits,
        "combo": 0,
        "inventory": ["packet_sniffer"],
        "relics": [],
        "effects": {"firewall": 0, "sandbox": 0, "incoming_hits": 0},
        "enemy": None,
        "pending": None,
        "room_options": [],
        "reward_kind": None,
        "reward_options": [],
        "shop_items": [],
        "event": None,
        "game_over": False,
        "won": False,
        "stats": {
            "questions_answered": 0, "correct_answers": 0, "damage_taken": 0,
            "enemies_defeated": 0, "items_used": 0,
        },
    }
    state = session["game_state"]
    state["enemy"] = create_enemy(1, relics=state["relics"])
    record_room(1)
    session.modified = True
    return jsonify({"status": "started", **public_state(state)})


@app.route("/api/state", methods=["GET"])
def get_state():
    state = session.get("game_state")
    if not state:
        return jsonify({"error": "No active run"}), 400
    return jsonify(public_state(state))


@app.route("/api/question", methods=["GET"])
def get_question():
    state = session.get("game_state")
    if not state or state.get("game_over") or not state.get("enemy") or state.get("pending"):
        return jsonify({"error": "No active combat question"}), 400
    question = current_question(state)
    tier = get_tier(state["current_room"])
    time_limit = 20 if "haste" in state["enemy"]["abilities"] else 30
    if question.get("domain") == "Networking" and "wireshark" in state["relics"]:
        time_limit += 5
    return jsonify({
        "tier": tier,
        "domain": question.get("domain", "General Security"),
        "question": question["question"],
        "options": question["options"],
        "time_limit": time_limit,
        **public_state(state),
    })


@app.route("/api/answer", methods=["POST"])
def submit_answer():
    state = session.get("game_state")
    if not state or state.get("game_over") or not state.get("enemy") or state.get("pending"):
        return jsonify({"error": "No active combat"}), 400

    data = request.get_json() or {}
    user_answer = data.get("answer")
    is_timeout = data.get("timeout", False)
    question = current_question(state)
    correct_answer = question.get("answer") or question.get("correct")
    tier = get_tier(state["current_room"])
    state["question_positions"][tier] += 1
    state["stats"]["questions_answered"] += 1
    enemy = state["enemy"]

    if is_timeout or user_answer != correct_answer:
        state["combo"] = 0
        state["effects"]["incoming_hits"] += 1
        blocked_by = None
        if state["effects"]["sandbox"]:
            state["effects"]["sandbox"] -= 1
            blocked_by = "Sandbox"
        elif state["effects"]["firewall"]:
            state["effects"]["firewall"] -= 1
            blocked_by = "Firewall"
        elif "zero_trust" in state["relics"] and state["effects"]["incoming_hits"] % 5 == 0:
            blocked_by = "Zero Trust"

        damage_taken = 0 if blocked_by else enemy["attack"] + (1 if "brutal" in enemy["abilities"] else 0)
        state["hp"] = max(0, state["hp"] - damage_taken)
        state["stats"]["damage_taken"] += damage_taken
        destroyed_item = remove_random_item(state) if "encryptor" in enemy["abilities"] else None
        if "credit_drain" in enemy["abilities"]:
            state["credits"] = max(0, state["credits"] - 20)
        if "leech" in enemy["abilities"] or "regenerate" in enemy["abilities"]:
            enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + 1)

        revived = False
        if state["hp"] == 0 and "backup" in state["inventory"]:
            state["inventory"].remove("backup")
            state["hp"] = 1
            revived = True
        if state["hp"] == 0:
            finish_failed_run(state)
            status = "game_over"
        else:
            status = "player_hit"
        session.modified = True
        return jsonify({
            "status": status, "was_timeout": is_timeout, "correct_answer": correct_answer,
            "explanation": question.get("explanation", ""), "damage_taken": damage_taken,
            "blocked_by": blocked_by, "destroyed_item": item_view(destroyed_item) if destroyed_item else None,
            "revived": revived, **public_state(state),
        })

    state["stats"]["correct_answers"] += 1
    state["combo"] += 1
    damage_dealt = 1
    if state["combo"] % 3 == 0:
        damage_dealt = 3 if "exploit_chain" in state["relics"] else 2
    if question.get("domain") == "Linux" and "tux_kernel" in state["relics"]:
        damage_dealt += 1
    if question.get("domain") == "Web Security" and "web_proxy" in state["relics"]:
        damage_dealt += 1
    armor_blocked = 0
    if enemy.get("armor", 0):
        armor_blocked = min(1, damage_dealt)
        damage_dealt -= armor_blocked
        enemy["armor"] = 0
    enemy["hp"] = max(0, enemy["hp"] - damage_dealt)
    credits_earned = 10 + (state["combo"] * 2) + (5 if "credit_miner" in state["relics"] else 0)
    state["credits"] += credits_earned
    status = complete_combat(state) if enemy["hp"] == 0 else "enemy_hit"
    session.modified = True
    return jsonify({
        "status": status, "correct_answer": correct_answer,
        "explanation": question.get("explanation", ""), "damage_dealt": damage_dealt,
        "armor_blocked": armor_blocked, "credits_earned": credits_earned,
        "defeated_enemy": enemy["name"] if enemy["hp"] == 0 else None,
        **public_state(state),
    })


@app.route("/api/route/choose", methods=["POST"])
def choose_route():
    state = session.get("game_state")
    room_type = (request.get_json() or {}).get("room_type")
    if not state or state.get("pending") != "route" or room_type not in state["room_options"]:
        return jsonify({"error": "Invalid room choice"}), 400
    start_room(state, room_type)
    session.modified = True
    return jsonify({"status": "room_selected", **public_state(state)})


@app.route("/api/reward/choose", methods=["POST"])
def choose_reward():
    state = session.get("game_state")
    reward_id = (request.get_json() or {}).get("reward_id")
    if not state or state.get("pending") != "reward":
        return jsonify({"error": "No reward is waiting"}), 400
    reward = next((entry for entry in state["reward_options"] if entry["id"] == reward_id), None)
    if not reward:
        return jsonify({"error": "Invalid reward"}), 400
    if reward["type"] == "item":
        if len(state["inventory"]) >= INVENTORY_LIMIT:
            return jsonify({"error": "Inventory full. Use or discard an item first."}), 400
        state["inventory"].append(reward_id)
        discover("items", reward_id)
    elif reward["type"] == "relic":
        if reward_id not in state["relics"]:
            state["relics"].append(reward_id)
        discover("relics", reward_id)
    else:
        state["credits"] += 50
    advance_stage(state)
    session.modified = True
    return jsonify({"status": "reward_collected", **public_state(state)})


@app.route("/api/heal/choose", methods=["POST"])
def choose_heal():
    state = session.get("game_state")
    choice = (request.get_json() or {}).get("choice")
    if not state or state.get("pending") != "heal" or choice not in {"repair", "upgrade"}:
        return jsonify({"error": "Invalid repair choice"}), 400
    if choice == "repair":
        state["hp"] = min(state["max_hp"], state["hp"] + 3)
    else:
        state["max_hp"] += 1
        state["hp"] = min(state["max_hp"], state["hp"] + 1)
    advance_stage(state)
    session.modified = True
    return jsonify({"status": "repaired", **public_state(state)})


@app.route("/api/shop/buy", methods=["POST"])
def buy_shop_item():
    state = session.get("game_state")
    item_id = (request.get_json() or {}).get("item_id")
    offered = [item["id"] for item in state.get("shop_items", [])] if state else []
    if not state or state.get("pending") != "shop" or item_id not in offered:
        return jsonify({"error": "Item is not available"}), 400
    item = ITEMS[item_id]
    if state["credits"] < item["price"]:
        return jsonify({"error": "Not enough credits"}), 400
    if len(state["inventory"]) >= INVENTORY_LIMIT:
        return jsonify({"error": "Inventory full"}), 400
    state["credits"] -= item["price"]
    state["inventory"].append(item_id)
    state["shop_items"] = [entry for entry in state["shop_items"] if entry["id"] != item_id]
    discover("items", item_id)
    session.modified = True
    return jsonify({"status": "purchased", **public_state(state)})


@app.route("/api/shop/leave", methods=["POST"])
def leave_shop():
    state = session.get("game_state")
    if not state or state.get("pending") != "shop":
        return jsonify({"error": "No active shop"}), 400
    advance_stage(state)
    session.modified = True
    return jsonify({"status": "shop_left", **public_state(state)})


@app.route("/api/event/choose", methods=["POST"])
def choose_event():
    state = session.get("game_state")
    choice = (request.get_json() or {}).get("choice")
    if not state or state.get("pending") != "event":
        return jsonify({"error": "No active event"}), 400
    event_id = state["event"]["id"]
    valid = {entry["id"] for entry in EVENTS[event_id]["choices"]}
    if choice not in valid:
        return jsonify({"error": "Invalid event choice"}), 400
    message = ""
    if event_id == "suspicious_usb" and choice == "scan":
        state["credits"] += 35
        message = "The scan found useful data. You gained 35 credits."
    elif event_id == "suspicious_usb":
        if random.random() < 0.6 and len(state["inventory"]) < INVENTORY_LIMIT:
            item_id = random.choice(list(ITEMS))
            state["inventory"].append(item_id)
            discover("items", item_id)
            message = f"The USB contained {ITEMS[item_id]['name']}."
        else:
            state["hp"] = max(1, state["hp"] - 1)
            message = "The USB contained malware. You lost 1 HP."
    elif event_id == "open_wifi" and choice == "monitor":
        state["credits"] += 25
        message = "Passive monitoring revealed useful intelligence. You gained 25 credits."
    elif event_id == "open_wifi":
        if random.random() < 0.5 and len(state["inventory"]) < INVENTORY_LIMIT:
            state["inventory"].append("packet_sniffer")
            discover("items", "packet_sniffer")
            message = "You captured a Packet Sniffer."
        else:
            state["hp"] = max(1, state["hp"] - 1)
            message = "The network was a trap. You lost 1 HP."
    elif event_id == "leaked_database" and choice == "report":
        state["hp"] = min(state["max_hp"], state["hp"] + 2)
        message = "Responsible disclosure restored 2 HP."
    elif event_id == "leaked_database":
        state["credits"] += 100
        state["hp"] = max(1, state["hp"] - 1)
        message = "You gained 100 credits but lost 1 HP."
    elif event_id == "legacy_server" and choice == "patch":
        cost = min(30, state["credits"])
        state["credits"] -= cost
        state["hp"] = min(state["max_hp"], state["hp"] + 2)
        message = f"You spent {cost} credits and restored 2 HP."
    else:
        if random.random() < 0.55 and len(state["inventory"]) < INVENTORY_LIMIT:
            item_id = random.choice(["zero_day", "backup", "sandbox"])
            state["inventory"].append(item_id)
            discover("items", item_id)
            message = f"The exploit succeeded. You found {ITEMS[item_id]['name']}."
        else:
            state["hp"] = max(1, state["hp"] - 2)
            message = "The exploit backfired. You lost 2 HP."
    advance_stage(state)
    session.modified = True
    return jsonify({"status": "event_resolved", "message": message, **public_state(state)})


@app.route("/api/item/use", methods=["POST"])
def use_item():
    state = session.get("game_state")
    item_id = (request.get_json() or {}).get("item_id")
    if not state or state.get("game_over") or item_id not in state["inventory"]:
        return jsonify({"error": "Item is not available"}), 400
    combat_only = {"packet_sniffer", "overclock", "zero_day"}
    if item_id in combat_only and (not state.get("enemy") or state.get("pending")):
        return jsonify({"error": "This item can only be used during combat"}), 400
    result = {"status": "item_used", "effect": item_id}
    if item_id == "packet_sniffer":
        if "jammer" in state["enemy"]["abilities"]:
            return jsonify({"error": "The enemy's Signal Jammer blocks Packet Sniffer"}), 400
        question = current_question(state)
        correct = question.get("answer") or question.get("correct")
        result["removed"] = random.sample([key for key in question["options"] if key != correct], 2)
    elif item_id == "firewall":
        state["effects"]["firewall"] += 1
    elif item_id == "health_patch":
        if state["hp"] == state["max_hp"]:
            return jsonify({"error": "HP is already full"}), 400
        state["hp"] = min(state["max_hp"], state["hp"] + 2)
    elif item_id == "overclock":
        result["add_time"] = 15
    elif item_id == "sandbox":
        state["effects"]["sandbox"] += 1
    elif item_id == "zero_day":
        enemy = state["enemy"]
        enemy["hp"] = max(0, enemy["hp"] - 2)
        result["damage_dealt"] = 2
        if enemy["hp"] == 0:
            result["status"] = complete_combat(state)
    elif item_id == "backup":
        return jsonify({"error": "Backup activates automatically when damage would defeat you"}), 400
    state["inventory"].remove(item_id)
    state["stats"]["items_used"] += 1
    session.modified = True
    return jsonify({**result, **public_state(state)})


@app.route("/api/item/discard", methods=["POST"])
def discard_item():
    state = session.get("game_state")
    item_id = (request.get_json() or {}).get("item_id")
    if not state or item_id not in state["inventory"]:
        return jsonify({"error": "Item is not available"}), 400
    state["inventory"].remove(item_id)
    session.modified = True
    return jsonify({"status": "discarded", **public_state(state)})


@app.route("/api/encyclopedia", methods=["GET"])
def encyclopedia():
    progress = get_progress()
    enemy_catalog = {}
    for enemies in NORMAL_ENEMIES.values():
        for enemy in enemies:
            enemy_catalog[enemy["id"]] = enemy
    for boss in BOSSES.values():
        enemy_catalog[boss["id"]] = boss
    return jsonify({
        "progress": {
            "runs_started": progress["runs_started"],
            "runs_completed": progress["runs_completed"],
            "best_room": progress["best_room"],
        },
        "mechanics": [{"id": key, **MECHANICS[key]} for key in progress["unlocked_mechanics"]],
        "items": [item_view(key) for key in progress["unlocked_items"]],
        "relics": [relic_view(key) for key in progress["unlocked_relics"]],
        "abilities": [ability_view(key) for key in progress["unlocked_abilities"]],
        "rooms": [room_view(key) for key in progress["unlocked_rooms"]],
        "enemies": [
            {
                "id": key, "name": enemy_catalog[key]["name"], "icon": enemy_catalog[key]["icon"],
                "kind": enemy_catalog[key].get("kind", "ENEMY"),
            }
            for key in progress["unlocked_enemies"]
        ],
        "locked_counts": {
            "items": len(ITEMS) - len(progress["unlocked_items"]),
            "relics": len(RELICS) - len(progress["unlocked_relics"]),
            "abilities": len(ABILITIES) - len(progress["unlocked_abilities"]),
            "rooms": len(ROOMS) - len(progress["unlocked_rooms"]),
            "enemies": len(enemy_catalog) - len(progress["unlocked_enemies"]),
            "mechanics": len(MECHANICS) - len(progress["unlocked_mechanics"]),
        },
    })


@app.route("/api/progress/reset", methods=["POST"])
def reset_progress():
    session.pop("game_state", None)
    session["meta_progress"] = default_progress()
    session.modified = True
    return jsonify({"status": "progress_reset"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

import json
import os
import random

from flask import Flask, has_request_context, jsonify, render_template, request, session


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

TOTAL_ROOMS = 15
INVENTORY_LIMIT = 4
PLAYER_MAX_HP = 7

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
        "description": "Block the first damaging enemy attack in every battle.",
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
        "description": "Can jam Packet Sniffer for the enemy's next two turns.",
    },
    "leech": {
        "name": "Data Leech", "icon": "🩸",
        "description": "Can spend a turn restoring 1 HP.",
    },
    "credit_drain": {
        "name": "Wallet Drain", "icon": "💸",
        "description": "Can spend a turn stealing up to 20 credits.",
    },
    "encryptor": {
        "name": "Encryption", "icon": "🔒",
        "description": "Can spend a turn destroying one random inventory item.",
    },
    "regenerate": {
        "name": "Self Repair", "icon": "♻️",
        "description": "Can spend a turn restoring 1 HP.",
    },
    "brutal": {
        "name": "Critical Strike", "icon": "💥",
        "description": "Uses more Heavy Attacks that deal additional damage.",
    },
}

INTENTS = {
    "attack": {"name": "Attack", "icon": "⚔️", "description": "Deal normal attack damage."},
    "heavy_attack": {"name": "Heavy Attack", "icon": "💥", "description": "Deal 1 more damage than a normal attack."},
    "defend": {"name": "Fortify", "icon": "🛡️", "description": "Gain 1 armor against the next hit."},
    "heal": {"name": "Self Repair", "icon": "♻️", "description": "Restore 1 HP, up to maximum HP."},
    "credit_drain": {"name": "Wallet Drain", "icon": "💸", "description": "Steal up to 20 credits."},
    "jammer": {"name": "Signal Jam", "icon": "📵", "description": "Disable Packet Sniffer for two turns."},
    "encrypt": {"name": "Encrypt", "icon": "🔒", "description": "Destroy one random inventory item."},
    "root_lock": {"name": "Root Lock", "icon": "👑", "description": "Reset combo and weaken the next player attack."},
}

NORMAL_ENEMIES = {
    "EASY": [
        {"id": "spam_bot", "name": "Spam Bot", "icon": "🤖", "abilities": ["credit_drain"], "description": "A noisy automated sender that tries to empty your wallet.", "strategy": "Exploit its Wallet Drain turn or defend when an attack is coming."},
        {"id": "phishing_email", "name": "Phishing Email", "icon": "📧", "abilities": ["jammer"], "description": "A deceptive message that disrupts your investigation tools.", "strategy": "Use Packet Sniffer before Signal Jam, or interrupt the jam with Exploit."},
        {"id": "adware_bug", "name": "Adware Bug", "icon": "🐛", "abilities": ["leech"], "description": "Persistent nuisance software that repairs itself between attacks.", "strategy": "Interrupt Self Repair or use Exploit to outpace its healing."},
    ],
    "MEDIUM": [
        {"id": "botnet_node", "name": "Botnet Node", "icon": "🧟", "abilities": ["shielded"], "description": "A hardened member of a larger compromised network.", "strategy": "Break its starting armor, then interrupt Fortify before it rebuilds defenses."},
        {"id": "credential_thief", "name": "Credential Thief", "icon": "🔓", "abilities": ["credit_drain"], "description": "A quick attacker that steals credits and follows with heavy damage.", "strategy": "Exploit Wallet Drain and defend against the following Heavy Attack."},
        {"id": "malware_loader", "name": "Malware Loader", "icon": "👾", "abilities": ["haste"], "description": "A fast payload installer that shortens every decision window.", "strategy": "Plan your action before reading the answers; its questions only allow 20 seconds."},
    ],
    "HARD": [
        {"id": "ransomware", "name": "Ransomware", "icon": "💀", "abilities": ["encryptor"], "description": "Destructive malware that targets both your health and inventory.", "strategy": "Interrupt Encrypt whenever you carry an important consumable."},
        {"id": "insider_threat", "name": "Insider Threat", "icon": "🕵️", "abilities": ["brutal"], "description": "A trusted user turned hostile, capable of repeated critical strikes.", "strategy": "Defend against Heavy Attacks and Exploit its Fortify turns."},
        {"id": "zero_day_exploit", "name": "Zero-Day Exploit", "icon": "🐉", "abilities": ["regenerate"], "description": "An unknown vulnerability that attacks hard and repairs itself.", "strategy": "Use Exploit on Self Repair and save defenses for Heavy Attacks."},
    ],
}

BOSSES = {
    5: {
        "id": "phishing_king", "name": "Phishing King", "icon": "🎣",
        "kind": "MINIBOSS", "max_hp": 7, "attack": 1, "abilities": ["jammer"],
        "description": "The ruler of deceptive messages, backed by an aggressive signal jammer.",
        "strategy": "At half HP it chains jams and heavy attacks. Interrupt the jam before using tools.",
    },
    10: {
        "id": "ransomware_overlord", "name": "Ransomware Overlord", "icon": "🦠",
        "kind": "MAJOR BOSS", "max_hp": 10, "attack": 1, "abilities": ["encryptor", "shielded"],
        "description": "An armored extortion engine that repeatedly threatens your inventory.",
        "strategy": "Remove its armor early. In phase two, prioritize interrupting Encrypt.",
    },
    15: {
        "id": "root_admin", "name": "The Root Admin", "icon": "👑",
        "kind": "FINAL BOSS", "max_hp": 14, "attack": 2,
        "abilities": ["haste", "regenerate"],
        "description": "The system's ultimate administrator, combining speed, damage, and recovery.",
        "strategy": "Watch every intent. Phase two adds Root Lock, so alternate Defend and Exploit carefully.",
    },
}

ENEMY_PATTERNS = {
    "spam_bot": [["attack", "credit_drain", "attack"]],
    "phishing_email": [["attack", "jammer", "attack"]],
    "adware_bug": [["attack", "heal", "attack"]],
    "botnet_node": [["attack", "defend", "heavy_attack"]],
    "credential_thief": [["attack", "credit_drain", "heavy_attack"]],
    "malware_loader": [["attack", "heavy_attack", "defend"]],
    "ransomware": [["attack", "encrypt", "heavy_attack"]],
    "insider_threat": [["attack", "heavy_attack", "defend"]],
    "zero_day_exploit": [["attack", "heal", "heavy_attack"]],
    "phishing_king": [["attack", "jammer", "attack"], ["heavy_attack", "jammer", "heavy_attack"]],
    "ransomware_overlord": [["attack", "encrypt", "defend"], ["encrypt", "heavy_attack", "defend"]],
    "root_admin": [["attack", "defend", "heal"], ["heavy_attack", "root_lock", "heal"]],
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
    "combat": {"name": "Active Quiz Combat", "description": "Choose Attack, Defend, or Exploit before answering. Enemy intents resolve after every question unless interrupted or defeated."},
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


def intent_view(intent_id, enemy=None):
    view = {"id": intent_id, **INTENTS[intent_id]}
    if enemy and intent_id in {"attack", "heavy_attack"}:
        view["amount"] = enemy["attack"] + (1 if intent_id == "heavy_attack" else 0)
    return view


def enemy_pattern(enemy):
    patterns = ENEMY_PATTERNS[enemy["id"]]
    return patterns[min(enemy.get("phase", 1) - 1, len(patterns) - 1)]


def set_enemy_intent(enemy):
    pattern = enemy_pattern(enemy)
    enemy["intent"] = pattern[enemy.get("turn", 0) % len(pattern)]


def advance_enemy_intent(enemy):
    previous_phase = enemy.get("phase", 1)
    if enemy["kind"] in {"MINIBOSS", "MAJOR BOSS", "FINAL BOSS"} and enemy["hp"] <= enemy["max_hp"] // 2:
        enemy["phase"] = 2
    if enemy.get("phase", 1) != previous_phase:
        enemy["turn"] = -1
    if enemy.get("jammer_turns", 0) > 0:
        enemy["jammer_turns"] -= 1
    enemy["turn"] = enemy.get("turn", 0) + 1
    set_enemy_intent(enemy)
    return enemy.get("phase", 1) != previous_phase


def create_enemy(room, elite=False, relics=None):
    if room in BOSSES and not elite:
        enemy = BOSSES[room].copy()
    else:
        template = random.choice(NORMAL_ENEMIES[get_tier(room)])
        base_hp = {"EASY": 2, "MEDIUM": 3, "HARD": 4}[get_tier(room)]
        enemy = {
            **template,
            "kind": "ELITE" if elite else "ENEMY",
            "max_hp": base_hp + 2 if elite else base_hp,
            "attack": 1,
        }
        if elite:
            extra = random.choice([ability for ability in ABILITIES if ability not in enemy["abilities"]])
            enemy["abilities"] = [*enemy["abilities"], extra]

    enemy["hp"] = enemy["max_hp"]
    enemy["armor"] = 1 if "shielded" in enemy["abilities"] else 0
    enemy["turn"] = 0
    enemy["phase"] = 1
    enemy["jammer_turns"] = 0
    enemy["zero_trust_available"] = True
    if "root_access" in (relics or []) and enemy["kind"] != "ENEMY":
        enemy["hp"] = max(1, enemy["hp"] - 1)
    set_enemy_intent(enemy)

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
        "intent_detail": intent_view(enemy["intent"], enemy),
        "pattern_details": [intent_view(intent_id, enemy) for intent_id in enemy_pattern(enemy)],
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


def revive_if_possible(state):
    if state["hp"] == 0 and "backup" in state["inventory"]:
        state["inventory"].remove("backup")
        state["hp"] = 1
        return True
    return False


def resolve_enemy_intent(state, combat_action, canceled=False):
    enemy = state["enemy"]
    intent_id = enemy["intent"]
    detail = intent_view(intent_id, enemy)
    result = {
        "id": intent_id, "name": detail["name"], "icon": detail["icon"],
        "canceled": canceled, "damage_taken": 0, "blocked_by": None,
        "destroyed_item": None,
    }
    if canceled:
        result["message"] = f"{detail['name']} was interrupted."
        return result

    if intent_id in {"attack", "heavy_attack"}:
        damage = enemy["attack"] + (1 if intent_id == "heavy_attack" else 0)
        if combat_action == "defend":
            damage = max(0, damage - 1)
        elif combat_action == "exploit":
            damage += 1
        if state["effects"]["sandbox"]:
            state["effects"]["sandbox"] -= 1
            result["blocked_by"] = "Sandbox"
        elif state["effects"]["firewall"]:
            state["effects"]["firewall"] -= 1
            result["blocked_by"] = "Firewall"
        elif "zero_trust" in state["relics"] and enemy.get("zero_trust_available", True):
            enemy["zero_trust_available"] = False
            result["blocked_by"] = "Zero Trust"
        if result["blocked_by"]:
            damage = 0
        state["hp"] = max(0, state["hp"] - damage)
        state["stats"]["damage_taken"] += damage
        result["damage_taken"] = damage
        result["message"] = f"{detail['name']} dealt {damage} damage."
    elif intent_id == "defend":
        enemy["armor"] = min(2, enemy.get("armor", 0) + 1)
        result["message"] = "The enemy gained 1 armor."
    elif intent_id == "heal":
        healed = min(1, enemy["max_hp"] - enemy["hp"])
        enemy["hp"] += healed
        result["message"] = f"The enemy restored {healed} HP."
    elif intent_id == "credit_drain":
        stolen = min(20, state["credits"])
        state["credits"] -= stolen
        result["message"] = f"The enemy stole {stolen} credits."
    elif intent_id == "jammer":
        # The turn-advance step happens immediately after this action, so 3
        # produces two complete future turns of jamming.
        enemy["jammer_turns"] = 3
        result["message"] = "Packet Sniffer is jammed for two turns."
    elif intent_id == "encrypt":
        destroyed = remove_random_item(state)
        result["destroyed_item"] = item_view(destroyed) if destroyed else None
        result["message"] = f"{ITEMS[destroyed]['name']} was destroyed." if destroyed else "Encryption found no item to destroy."
    elif intent_id == "root_lock":
        state["combo"] = 0
        state["effects"]["root_lock"] = 1
        result["message"] = "Your combo was reset and your next attack is weakened."
    return result


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
        "effects": {"firewall": 0, "sandbox": 0, "root_lock": 0},
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
    combat_action = data.get("combat_action", "attack")
    if combat_action not in {"attack", "defend", "exploit"}:
        return jsonify({"error": "Choose Attack, Defend, or Exploit"}), 400
    question = current_question(state)
    correct_answer = question.get("answer") or question.get("correct")
    tier = get_tier(state["current_room"])
    state["question_positions"][tier] += 1
    state["stats"]["questions_answered"] += 1
    enemy = state["enemy"]
    is_correct = not is_timeout and user_answer == correct_answer
    damage_dealt = 0
    armor_blocked = 0
    credits_earned = 0
    enemy_action = None
    phase_changed = False

    if is_correct:
        state["stats"]["correct_answers"] += 1
        state["combo"] += 1
        if combat_action in {"attack", "exploit"}:
            base_damage = 1
            if state["combo"] % 3 == 0:
                base_damage = 3 if "exploit_chain" in state["relics"] else 2
            if question.get("domain") == "Linux" and "tux_kernel" in state["relics"]:
                base_damage += 1
            if question.get("domain") == "Web Security" and "web_proxy" in state["relics"]:
                base_damage += 1
            if state["effects"].get("root_lock"):
                base_damage = max(0, base_damage - 1)
                state["effects"]["root_lock"] = 0
            damage_dealt = base_damage * (2 if combat_action == "exploit" else 1)
            armor_blocked = min(enemy.get("armor", 0), damage_dealt)
            damage_dealt -= armor_blocked
            enemy["armor"] = max(0, enemy.get("armor", 0) - armor_blocked)
            enemy["hp"] = max(0, enemy["hp"] - damage_dealt)
        credits_earned = 10 + (state["combo"] * 2) + (5 if "credit_miner" in state["relics"] else 0)
        state["credits"] += credits_earned
    else:
        state["combo"] = 0

    defeated_enemy = enemy["name"] if enemy["hp"] == 0 else None
    if enemy["hp"] == 0:
        status = complete_combat(state)
    else:
        canceled = is_correct and combat_action in {"defend", "exploit"}
        enemy_action = resolve_enemy_intent(state, combat_action, canceled=canceled)
        revived = revive_if_possible(state)
        if state["hp"] == 0:
            finish_failed_run(state)
            status = "game_over"
        else:
            phase_changed = advance_enemy_intent(enemy)
            status = "enemy_hit" if is_correct else "player_hit"

    revived = locals().get("revived", False)
    session.modified = True
    return jsonify({
        "status": status, "is_correct": is_correct, "was_timeout": is_timeout,
        "combat_action": combat_action, "correct_answer": correct_answer,
        "explanation": question.get("explanation", ""), "damage_dealt": damage_dealt,
        "armor_blocked": armor_blocked, "credits_earned": credits_earned,
        "damage_taken": enemy_action["damage_taken"] if enemy_action else 0,
        "blocked_by": enemy_action["blocked_by"] if enemy_action else None,
        "destroyed_item": enemy_action["destroyed_item"] if enemy_action else None,
        "enemy_action": enemy_action, "revived": revived,
        "phase_changed": phase_changed, "defeated_enemy": defeated_enemy,
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
        if state["enemy"].get("jammer_turns", 0) > 0:
            return jsonify({"error": "Packet Sniffer is currently jammed"}), 400
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
                "description": enemy_catalog[key]["description"],
                "strategy": enemy_catalog[key]["strategy"],
                "max_hp": enemy_catalog[key]["max_hp"] if "max_hp" in enemy_catalog[key] else next(
                    {"EASY": 2, "MEDIUM": 3, "HARD": 4}[tier]
                    for tier, enemies in NORMAL_ENEMIES.items()
                    if any(entry["id"] == key for entry in enemies)
                ),
                "attack": enemy_catalog[key].get("attack", 1),
                "abilities": [ability_view(ability) for ability in enemy_catalog[key]["abilities"]],
                "patterns": [
                    [intent_view(intent_id) for intent_id in pattern]
                    for pattern in ENEMY_PATTERNS[key]
                ],
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

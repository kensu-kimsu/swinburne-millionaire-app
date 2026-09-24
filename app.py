import json
import math
import os
import random

from flask import Flask, has_request_context, jsonify, render_template, request, session


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

TOTAL_ROOMS = 15
INVENTORY_LIMIT = 4
PLAYER_MAX_HP = 12
ELITE_SPAWN_CHANCE = 0.22

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
        "description": "Every third correct answer adds 2 damage instead of 1.",
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
        "description": "Questions begin with only 30 seconds.",
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
    "tidal_prison": {
        "name": "Tidal Prison", "icon": "🌊",
        "description": "Abyssal magic damages you and submerges the answers for 3 seconds.",
    },
    "petrify": {
        "name": "Petrification", "icon": "🗿",
        "description": "Death turns the answer grid to stone for 5 seconds.",
    },
    "inferno": {
        "name": "Dragon Inferno", "icon": "☄️",
        "description": "A devastating meteor strike deals heavy damage and scorches the answers.",
    },
    "time_stop": {
        "name": "Time Stop", "icon": "⌛",
        "description": "Root magic freezes the answer grid for 6 seconds while the timer continues.",
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
    "tsunami": {"name": "Abyssal Tsunami", "icon": "🌊", "description": "Deal boss damage and submerge the next answer grid."},
    "petrify": {"name": "Petrifying Gaze", "icon": "🗿", "description": "Turn the next answer grid to stone."},
    "meteor": {"name": "Root Meteor", "icon": "☄️", "description": "Deal catastrophic dragon damage and scorch the next answer grid."},
    "time_stop": {"name": "Time Stop", "icon": "⌛", "description": "Freeze the next answer grid while its timer continues."},
}

NORMAL_ENEMIES = {
    "EASY": [
        {"id": "spam_bot", "name": "Spam Bot", "icon": "🤖", "abilities": ["credit_drain"], "description": "A manic cyber-goblin courier whose dish-pack floods the dungeon with junk messages.", "strategy": "Exploit its Wallet Drain turn or defend when an attack is coming."},
        {"id": "phishing_email", "name": "Phishing Mimic", "icon": "📧", "abilities": ["jammer"], "description": "A cursed envelope mimic that lures travellers with false login lights.", "strategy": "Use Packet Sniffer before Signal Jam, or interrupt the jam with Exploit."},
        {"id": "adware_bug", "name": "Adware Scarab", "icon": "🐛", "abilities": ["leech"], "description": "A chrome scarab covered in intrusive illusion-panels that continually repairs its shell.", "strategy": "Interrupt Self Repair or use Exploit to outpace its healing."},
    ],
    "MEDIUM": [
        {"id": "botnet_node", "name": "Botnet Golem", "icon": "🧟", "abilities": ["shielded"], "description": "An undead network golem whose server-heart commands a swarm of cable-bound skulls.", "strategy": "Break its starting armor, then interrupt Fortify before it rebuilds defenses."},
        {"id": "credential_thief", "name": "Credential Panther", "icon": "🔓", "abilities": ["credit_drain"], "description": "A masked shadow panther that stalks access keys and vanishes into corrupted smoke.", "strategy": "Exploit Wallet Drain and defend against the following Heavy Attack."},
        {"id": "malware_loader", "name": "Payload Ogre", "icon": "👾", "abilities": ["haste"], "description": "A furnace-bellied cyber-ogre carrying cursed payload cores and an infernal launcher.", "strategy": "Plan your action before reading the answers; its questions only allow 30 seconds."},
    ],
    "HARD": [
        {"id": "ransomware", "name": "Ransom Lich", "icon": "💀", "abilities": ["encryptor"], "description": "A chained cyber-lich fused to a mechanical spider body that seals relics in red data-fire.", "strategy": "Interrupt Encrypt whenever you carry an important consumable."},
        {"id": "insider_threat", "name": "Insider Werewolf", "icon": "🕵️", "abilities": ["brutal"], "description": "A corrupted werewolf knight wearing the shattered armor of a trusted guardian.", "strategy": "Defend against Heavy Attacks and Exploit its Fortify turns."},
        {"id": "zero_day_exploit", "name": "Zero-Day Hydra", "icon": "🐉", "abilities": ["regenerate"], "description": "A three-headed void hydra whose fragmented body rewrites itself faster than it can be studied.", "strategy": "Use Exploit on Self Repair and save defenses for Heavy Attacks."},
    ],
}

BOSSES = {
    5: {
        "id": "phishing_king", "name": "Cyber Leviathan", "icon": "🐋",
        "kind": "MINIBOSS", "max_hp": 7, "attack": 2, "abilities": ["tidal_prison", "jammer"],
        "description": "An abyssal sea-dragon fused with submarine armor, sonar arrays, and cable tentacles.",
        "strategy": "Its Tsunami damages you and hides the next answers. Defend or Exploit when danger is telegraphed.",
    },
    10: {
        "id": "ransomware_overlord", "name": "Death Protocol", "icon": "☠️",
        "kind": "MAJOR BOSS", "max_hp": 10, "attack": 3, "abilities": ["petrify", "encryptor", "shielded"],
        "description": "Death itself reborn as a cybernetic reaper, wielding a violet plasma scythe against your inventory.",
        "strategy": "Remove its armor early. Interrupt Petrifying Gaze or lose five seconds of answering time.",
    },
    15: {
        "id": "root_admin", "name": "The Root Dragon", "icon": "🐉",
        "kind": "FINAL BOSS", "max_hp": 14, "attack": 4,
        "abilities": ["inferno", "time_stop", "haste", "regenerate"],
        "description": "An ancient obsidian dragon crowned in root-access circuitry—the apex intelligence of the dungeon.",
        "strategy": "Meteor can deal 6 damage and Time Stop steals six seconds. Save Focus for dangerous warnings.",
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
    "phishing_king": [["attack", "tsunami", "heavy_attack"], ["tsunami", "heavy_attack", "jammer"]],
    "ransomware_overlord": [["attack", "petrify", "defend"], ["petrify", "heavy_attack", "encrypt"]],
    "root_admin": [["meteor", "defend", "heal"], ["heavy_attack", "time_stop", "meteor"]],
}

ROOMS = {
    "combat": {"name": "Combat", "icon": "⚔️", "description": "Fight a normal enemy."},
    "elite": {"name": "Elite Ambush", "icon": "💀", "description": "A 22% surprise upgrade to a Combat encounter, with more HP, damage, and abilities."},
    "loot": {"name": "Data Cache", "icon": "🎁", "description": "Choose a free consumable or credits without advancing the stage."},
    "heal": {"name": "Repair Station", "icon": "❤️", "description": "Restore or improve HP without advancing the stage."},
    "shop": {"name": "Dark Web Market", "icon": "🛒", "description": "Buy consumables between combat stages."},
    "event": {"name": "Unknown Signal", "icon": "❓", "description": "Take a risk between fights without advancing the stage."},
    "boss": {"name": "Boss", "icon": "👑", "description": "A powerful enemy with special abilities."},
}

MECHANICS = {
    "combat": {"name": "Active Quiz Combat", "description": "Enemy actions are hidden. Attack builds Focus and softens incoming damage; spend 2 Focus on Exploit."},
    "combo": {"name": "Combo Damage", "description": "Every third consecutive correct answer deals additional damage."},
    "routes": {"name": "Route Choices", "description": "Support rooms happen between fights. Only completed combat advances the 15 stages."},
    "inventory": {"name": "Inventory", "description": "Carry up to four consumable items and choose when to use them."},
    "loot": {"name": "Loot", "description": "Defeated enemies and data caches offer a choice of rewards."},
    "relics": {"name": "Relics", "description": "Relics provide passive bonuses that last for the entire run."},
    "shops": {"name": "Shops", "description": "Credits earned in combat can purchase useful consumables."},
    "events": {"name": "Random Events", "description": "Events offer choices that can produce rewards or penalties."},
    "elites": {"name": "Elite Enemies", "description": "Elites have more HP and abilities but provide stronger rewards."},
    "bosses": {"name": "Boss Battles", "description": "Bosses have multiple HP, stronger attacks, and unique abilities."},
    "progression": {"name": "Discovery Progress", "description": "Enemies, items, relics, rooms, and abilities appear in the encyclopedia after discovery."},
    "recovery": {"name": "Combat Recovery", "description": "Defeating an enemy restores 1 HP, rewarding aggressive but controlled play."},
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


def create_enemy(room, elite=False, relics=None, enemy_id=None):
    if room in BOSSES and not elite and (enemy_id is None or enemy_id == BOSSES[room]["id"]):
        enemy = BOSSES[room].copy()
    else:
        candidates = NORMAL_ENEMIES[get_tier(room)]
        template = next((entry for entry in candidates if entry["id"] == enemy_id), None)
        template = template or random.choice(candidates)
        base_hp = {"EASY": 3, "MEDIUM": 4, "HARD": 5}[get_tier(room)]
        enemy = {
            **template,
            "kind": "ELITE" if elite else "ENEMY",
            "max_hp": base_hp + 2 if elite else base_hp,
            "attack": 2 if elite else 1,
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


def _maze_floor(width=9, height=7):
    """Create a compact connected dungeon using randomized depth-first carving."""
    grid = [["#" for _ in range(width)] for _ in range(height)]
    stack = [(1, 1)]
    grid[1][1] = "."
    while stack:
        x, y = stack[-1]
        directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 < nx < width - 1 and 0 < ny < height - 1 and grid[ny][nx] == "#":
                grid[y + dy // 2][x + dx // 2] = "."
                grid[ny][nx] = "."
                stack.append((nx, ny))
                break
        else:
            stack.pop()
    return ["".join(row) for row in grid]


def _floor_distances(tiles, start):
    queue = [start]
    distances = {start: 0}
    for x, y in queue:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            point = (x + dx, y + dy)
            if point not in distances and tiles[point[1]][point[0]] == ".":
                distances[point] = distances[(x, y)] + 1
                queue.append(point)
    return distances


# Each entry is an authored arena. Rectangles are x, y, width, height in world units.
# They leave winding routes around the center rather than a straight lane to the exit.
LEVEL_LAYOUTS = (
    ((4, 2, 2, 4), (8, 6, 2, 3), (12, 1, 2, 4), (13, 7, 2, 2)),
    ((3, 4, 3, 2), (7, 1, 2, 4), (10, 6, 3, 2), (14, 3, 2, 3)),
    ((4, 1, 2, 4), (6, 7, 3, 2), (10, 3, 2, 4), (14, 6, 2, 2)),
    ((3, 3, 2, 4), (7, 6, 2, 3), (10, 1, 3, 3), (14, 4, 2, 3)),
    ((3, 2, 2, 3), (4, 7, 3, 2), (12, 7, 3, 2), (14, 2, 2, 3)),
    ((3, 2, 3, 3), (7, 6, 2, 3), (11, 1, 2, 4), (14, 7, 2, 2)),
    ((3, 5, 3, 2), (7, 2, 2, 3), (11, 6, 3, 2), (14, 2, 2, 3)),
    ((4, 2, 2, 4), (7, 7, 3, 2), (11, 3, 2, 3), (14, 6, 2, 2)),
    ((3, 3, 2, 3), (6, 7, 3, 2), (10, 1, 2, 4), (14, 5, 2, 3)),
    ((3, 2, 2, 4), (5, 7, 3, 2), (12, 7, 3, 2), (14, 2, 2, 4)),
    ((4, 1, 2, 4), (7, 6, 3, 3), (11, 2, 2, 4), (14, 7, 2, 2)),
    ((3, 4, 2, 3), (6, 1, 3, 3), (10, 6, 2, 3), (14, 2, 2, 4)),
    ((4, 2, 2, 4), (7, 7, 2, 2), (10, 2, 3, 3), (14, 6, 2, 3)),
    ((3, 2, 3, 3), (7, 5, 2, 4), (11, 1, 2, 4), (14, 7, 2, 2)),
    ((3, 2, 2, 4), (4, 7, 3, 2), (12, 7, 3, 2), (14, 2, 2, 4)),
)


def walkable(dungeon, x, y, clearance=.23):
    if not (clearance < x < dungeon["width"] - clearance and clearance < y < dungeon["height"] - clearance):
        return False
    return all(not (ox - clearance < x < ox + width + clearance and
                    oy - clearance < y < oy + height + clearance)
               for ox, oy, width, height in dungeon["obstacles"])


def create_dungeon_floor(state):
    """Load one of the fifteen fixed maps; encounters and chest chances vary."""
    stage = state["current_room"]
    boss_floor = stage in BOSSES
    theme = {5: "atlantis", 10: "graveyard", 15: "inferno"}.get(stage)
    if not theme:
        theme = ("catacomb", "temple", "foundry")[(stage - 1) // 5]
    enemies = []
    if boss_floor:
        boss = BOSSES[stage]
        enemies.append({
            "uid": f"s{stage}-boss", "x": 9, "y": 5.5,
            "enemy_id": boss["id"], "name": boss["name"],
            "elite": False, "kind": boss["kind"], "defeated": False,
        })
    else:
        candidate_pool = ((6.5, 5.5), (9.5, 5.5), (13.5, 5.5), (6.5, 1.2),
                          (9.5, 1.2), (13.5, 9.7), (16.5, 6.0), (9.5, 9.7))
        obstacles = LEVEL_LAYOUTS[stage - 1]
        arena = {"width": 18, "height": 11, "obstacles": obstacles}
        candidates = [(x, y) for x, y in candidate_pool
                      if walkable(arena, x, y, .5) and any(
                          not walkable(arena, 1.5 + (x - 1.5) * step / 32,
                                       9.5 + (y - 9.5) * step / 32)
                          for step in range(1, 32))][:3]
        for index in range(3):
            template = random.choice(NORMAL_ENEMIES[get_tier(stage)])
            x, y = candidates[index]
            elite = random.random() < ELITE_SPAWN_CHANCE
            enemies.append({
                "uid": f"s{stage}-e{index}", "x": x, "y": y,
                "vx": random.uniform(-1, 1), "vy": random.uniform(-1, 1),
                "enemy_id": template["id"], "name": template["name"],
                "elite": elite, "kind": "ELITE" if elite else "ENEMY", "defeated": False,
            })
    decor = [{"x": round(random.uniform(.75, 17.25), 2),
              "y": round(random.uniform(1, 10), 2),
              "kind": random.choice(["fire", "mist", "rune", "sparks"]),
              "phase": random.random() * 6.28} for _ in range(16)]
    chest_candidates = ((8, 1.3), (3, 1.3), (11, 9.7), (15, 9.7))
    chest_x, chest_y = next((x, y) for x, y in chest_candidates if all(
        not (ox - .4 < x < ox + width + .4 and oy - .4 < y < oy + height + .4)
        for ox, oy, width, height in LEVEL_LAYOUTS[stage - 1]))
    state["dungeon"] = {
        "width": 18, "height": 11, "theme": theme, "mode": "combat", "layout_id": stage,
        "seed": random.randint(0, 999999999), "obstacles": LEVEL_LAYOUTS[stage - 1],
        "player": {"x": 1.5, "y": 9.5}, "exit": {"x": 16.5, "y": 1.5},
        "enemies": enemies, "decor": decor,
        "chests": [{"x": chest_x, "y": chest_y, "opened": False}] if not boss_floor and random.random() < .38 else [],
        "feature": None,
    }
    state["enemy"] = None
    state["current_enemy_uid"] = None
    state["pending"] = "dungeon"
    state["return_to_dungeon_after_reward"] = False
    state["room_options"] = []
    discover("rooms", "combat")


def create_market_floor(state):
    """An optional interlude between levels; current_room remains unchanged."""
    state["dungeon"] = {
        "width": 18, "height": 11, "theme": "market", "mode": "market", "layout_id": "market",
        "seed": random.randint(0, 999999999),
        "obstacles": ((4, 2, 2, 3), (7, 6, 2, 3), (11, 2, 2, 3), (14, 7, 2, 2)),
        "player": {"x": 1.5, "y": 9.5}, "exit": {"x": 16.5, "y": 1.5},
        "enemies": [], "chests": [], "decor": [
            {"x": x, "y": y, "kind": "fire", "phase": x} for x, y in ((3, 3), (8, 5), (13, 4), (15, 8))],
        "feature": {"x": 15, "y": 3, "type": "shop", "used": False},
    }
    state["pending"] = "dungeon"


def dungeon_view(state):
    dungeon = state.get("dungeon")
    if not dungeon:
        return None
    remaining = sum(not enemy["defeated"] for enemy in dungeon["enemies"])
    return {**dungeon, "remaining": remaining, "exit_unlocked": remaining == 0}


def return_to_dungeon(state):
    state["enemy"] = None
    state["current_enemy_uid"] = None
    state["pending"] = "dungeon"
    state["reward_options"] = []
    state["shop_items"] = []
    state["event"] = None
    state["advance_after_reward"] = False
    state["return_to_dungeon_after_reward"] = False


def advance_dungeon_floor(state):
    state["current_room"] += 1
    record_room(state["current_room"])
    state["reward_options"] = []
    state["shop_items"] = []
    state["event"] = None
    state["support_used"] = False
    state["advance_after_reward"] = False
    create_dungeon_floor(state)


def activate_dungeon_feature(state, feature):
    feature["used"] = True
    feature_type = feature["type"]
    discover("rooms", feature_type)
    if feature_type == "shop":
        state["pending"] = "shop"
        state["shop_items"] = build_shop()
        discover("mechanics", "shops")
    elif feature_type == "heal":
        state["pending"] = "heal"
    else:
        state["pending"] = "event"
        event_id = random.choice(list(EVENTS))
        state["event"] = {"id": event_id, **EVENTS[event_id]}
        discover("mechanics", "events")


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
    public = {key: value for key, value in enemy.items() if key != "intent"}
    return {
        **public,
        "ability_details": [ability_view(ability) for ability in enemy["abilities"]],
        "intent_hidden": True,
    }


def threat_warning(state):
    enemy = state.get("enemy")
    if not enemy:
        return None
    intent_id = enemy["intent"]
    if intent_id in {"attack", "heavy_attack", "tsunami", "meteor"}:
        bonus = 1 if intent_id == "heavy_attack" else 2 if intent_id == "meteor" else 0
        damage = enemy["attack"] + bonus
        if damage >= state["hp"]:
            return {
                "level": "fatal", "label": "LETHAL THREAT",
                "description": "The next enemy action could defeat you. Defend or Exploit.",
            }
        if intent_id in {"heavy_attack", "tsunami", "meteor"}:
            return {
                "level": "danger", "label": "MENACING ATTACK",
                "description": "A powerful attack or spell is being prepared. Defend or Exploit to interrupt it.",
            }
    if intent_id in {"encrypt", "root_lock", "petrify", "time_stop"}:
        return {
            "level": "danger", "label": "DANGEROUS TECHNIQUE",
            "description": "The enemy is preparing a major special action.",
        }
    return {
        "level": "hidden", "label": "ACTION HIDDEN",
        "description": "The enemy is preparing its turn.",
    }


def public_state(state):
    return {
        "room": state["current_room"],
        "total_rooms": TOTAL_ROOMS,
        "hp": state["hp"],
        "max_hp": state["max_hp"],
        "credits": state["credits"],
        "combo": state["combo"],
        "focus": state.get("focus", 0),
        "max_focus": 2,
        "inventory_limit": INVENTORY_LIMIT,
        "inventory": [item_view(item) for item in state["inventory"]],
        "relics": [relic_view(relic) for relic in state["relics"]],
        "effects": state["effects"],
        "enemy": public_enemy(state.get("enemy")),
        "threat_warning": threat_warning(state),
        "pending": state.get("pending"),
        "room_options": [room_view(room) for room in state.get("room_options", [])],
        "reward_kind": state.get("reward_kind"),
        "reward_options": state.get("reward_options", []),
        "shop_items": state.get("shop_items", []),
        "event": state.get("event"),
        "stats": state["stats"],
        "game_over": state["game_over"],
        "won": state.get("won", False),
        "answer_lock": state.get("answer_lock", 0),
        "answer_lock_source": state.get("answer_lock_source"),
        "dungeon": dungeon_view(state),
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


def set_reward(state, kind, advance_after=False):
    state["pending"] = "reward"
    state["reward_kind"] = kind
    state["advance_after_reward"] = advance_after
    state["reward_options"] = choose_relic_rewards() if kind == "relic" else choose_item_rewards()
    discover("mechanics", "loot")


def generate_room_options(support_used=False):
    if support_used:
        choices = ["combat"]
    else:
        choices = ["combat", random.choice(["loot", "heal", "shop", "event"])]
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
    state["support_used"] = False
    state["advance_after_reward"] = False
    if state["current_room"] in BOSSES:
        state["enemy"] = create_enemy(state["current_room"], relics=state["relics"])
        discover("rooms", "boss")
        discover("mechanics", "bosses")
    else:
        state["pending"] = "route"
        state["room_options"] = generate_room_options()


def return_to_stage_route(state):
    state["enemy"] = None
    state["pending"] = "route"
    state["reward_options"] = []
    state["shop_items"] = []
    state["event"] = None
    state["support_used"] = True
    state["advance_after_reward"] = False
    state["room_options"] = generate_room_options(support_used=True)


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
        elite = random.random() < ELITE_SPAWN_CHANCE
        state["enemy"] = create_enemy(state["current_room"], elite=elite, relics=state["relics"])
        if elite:
            discover("mechanics", "elites")
    elif room_type == "loot":
        set_reward(state, "item", advance_after=False)
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
    defeated_kind = enemy["kind"]
    state["stats"]["enemies_defeated"] += 1
    state["hp"] = min(state["max_hp"], state["hp"] + 1)
    discover("mechanics", "recovery")
    dungeon = state.get("dungeon")
    encounter_uid = state.get("current_enemy_uid")
    if dungeon and encounter_uid:
        marker = next((entry for entry in dungeon["enemies"] if entry["uid"] == encounter_uid), None)
        if marker:
            marker["defeated"] = True
    state["enemy"] = None
    remaining = sum(not entry["defeated"] for entry in dungeon["enemies"]) if dungeon else 0
    if state["current_room"] == TOTAL_ROOMS and (not dungeon or not encounter_uid or remaining == 0):
        state["game_over"] = True
        state["won"] = True
        state["pending"] = "complete"
        progress = get_progress()
        progress["runs_completed"] += 1
        record_room(TOTAL_ROOMS)
        return "won"

    if defeated_kind in {"MINIBOSS", "MAJOR BOSS", "FINAL BOSS"}:
        if "incident_response" in state["relics"]:
            state["hp"] = min(state["max_hp"], state["hp"] + 1)
    if dungeon:
        return_to_dungeon(state)
        return "enemy_defeated"
    if defeated_kind in {"MINIBOSS", "MAJOR BOSS", "FINAL BOSS"}:
        set_reward(state, "relic", advance_after=not bool(dungeon))
    elif defeated_kind == "ELITE":
        if random.random() < 0.4:
            set_reward(state, "relic", advance_after=not bool(dungeon))
        else:
            set_reward(state, "item", advance_after=not bool(dungeon))
    else:
        set_reward(state, "item", advance_after=not bool(dungeon))
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
        "enemy_id": enemy["id"],
        "canceled": canceled, "damage_taken": 0, "blocked_by": None,
        "destroyed_item": None, "answer_lock_seconds": 0,
    }
    if canceled:
        result["message"] = f"{detail['name']} was interrupted."
        return result

    def apply_incoming_damage(base_damage):
        damage = base_damage
        if combat_action == "defend":
            damage = max(0, damage - 1)
        elif combat_action == "exploit":
            damage += 1
        if damage > 0:
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
        return damage

    if intent_id in {"attack", "heavy_attack"}:
        damage = apply_incoming_damage(enemy["attack"] + (1 if intent_id == "heavy_attack" else 0))
        result["message"] = f"{detail['name']} dealt {damage} damage."
    elif intent_id == "tsunami":
        damage = apply_incoming_damage(enemy["attack"])
        state["answer_lock"] = 3
        state["answer_lock_source"] = "SUBMERGED BY THE LEVIATHAN"
        result["answer_lock_seconds"] = 3
        result["message"] = f"The tsunami dealt {damage} damage and submerged the next answers for 3 seconds."
    elif intent_id == "petrify":
        state["answer_lock"] = 5
        state["answer_lock_source"] = "PETRIFIED BY DEATH"
        result["answer_lock_seconds"] = 5
        result["message"] = "Death's gaze petrified the next answer grid for 5 seconds."
    elif intent_id == "meteor":
        damage = apply_incoming_damage(enemy["attack"] + 2)
        state["answer_lock"] = 3
        state["answer_lock_source"] = "SCORCHED BY ROOT METEOR"
        result["answer_lock_seconds"] = 3
        result["message"] = f"Root Meteor dealt {damage} damage and scorched the next answers for 3 seconds."
    elif intent_id == "time_stop":
        state["answer_lock"] = 6
        state["answer_lock_source"] = "TIME FROZEN BY THE ROOT DRAGON"
        result["answer_lock_seconds"] = 6
        result["message"] = "The Root Dragon stopped time around the next answer grid for 6 seconds."
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
        "focus": 0,
        "inventory": ["packet_sniffer"],
        "relics": [],
        "effects": {"firewall": 0, "sandbox": 0, "root_lock": 0},
        "answer_lock": 0,
        "answer_lock_source": None,
        "enemy": None,
        "pending": None,
        "room_options": [],
        "reward_kind": None,
        "reward_options": [],
        "shop_items": [],
        "event": None,
        "support_used": False,
        "advance_after_reward": False,
        "return_to_dungeon_after_reward": False,
        "current_enemy_uid": None,
        "dungeon": None,
        "game_over": False,
        "won": False,
        "stats": {
            "questions_answered": 0, "correct_answers": 0, "damage_taken": 0,
            "enemies_defeated": 0, "items_used": 0,
        },
    }
    state = session["game_state"]
    create_dungeon_floor(state)
    record_room(1)
    session.modified = True
    return jsonify({"status": "started", **public_state(state)})


@app.route("/api/state", methods=["GET"])
def get_state():
    state = session.get("game_state")
    if not state:
        return jsonify({"error": "No active run"}), 400
    return jsonify(public_state(state))


@app.route("/api/dungeon/move", methods=["POST"])
def move_in_dungeon():
    state = session.get("game_state")
    data = request.get_json(silent=True) or {}
    if not state or state.get("pending") != "dungeon":
        return jsonify({"error": "The dungeon cannot be moved through right now."}), 400
    dungeon = state["dungeon"]
    try:
        x, y = float(data["x"]), float(data["y"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Movement requires x and y positions."}), 400
    if not all(map(math.isfinite, (x, y))):
        return jsonify({"error": "Movement requires finite positions."}), 400
    player = dungeon["player"]
    dx, dy = x - player["x"], y - player["y"]
    distance = math.hypot(dx, dy)
    if distance > .48:
        dx, dy = dx / distance * .48, dy / distance * .48
    next_x = player["x"] + dx
    next_y = player["y"] + dy
    if not walkable(dungeon, next_x, next_y):
        if walkable(dungeon, next_x, player["y"]):
            next_y = player["y"]
        elif walkable(dungeon, player["x"], next_y):
            next_x = player["x"]
        else:
            next_x, next_y = player["x"], player["y"]
    player["x"], player["y"] = round(next_x, 3), round(next_y, 3)
    marker = next((enemy for enemy in dungeon["enemies"] if not enemy["defeated"]
                   and math.hypot(enemy["x"] - player["x"], enemy["y"] - player["y"]) <
                   (0.88 if "BOSS" in enemy["kind"] else .52)), None)
    if marker:
        start_dungeon_encounter(state, marker)
        session.modified = True
        return jsonify({"status": "encounter_started", **public_state(state)})
    for chest in dungeon.get("chests", []):
        if not chest["opened"] and math.hypot(chest["x"] - player["x"], chest["y"] - player["y"]) < .48:
            chest["opened"] = True
            set_reward(state, "relic" if random.random() < .2 else "item")
            state["return_to_dungeon_after_reward"] = True
            session.modified = True
            return jsonify({"status": "chest_opened", **public_state(state)})
    feature = dungeon.get("feature")
    if feature and not feature["used"] and math.hypot(feature["x"] - player["x"], feature["y"] - player["y"]) < .42:
        activate_dungeon_feature(state, feature)
        session.modified = True
        return jsonify({"status": "feature_found", **public_state(state)})
    exit_point = dungeon["exit"]
    if math.hypot(exit_point["x"] - player["x"], exit_point["y"] - player["y"]) < .55:
        remaining = sum(not enemy["defeated"] for enemy in dungeon["enemies"])
        if remaining:
            session.modified = True
            return jsonify({"status": "exit_locked", "message": f"Defeat {remaining} remaining enemies to unlock the gate.", **public_state(state)})
        if state["current_room"] < TOTAL_ROOMS:
            if dungeon.get("mode") == "market" or random.random() >= .3:
                advance_dungeon_floor(state)
            else:
                create_market_floor(state)
            session.modified = True
            return jsonify({"status": "floor_advanced", **public_state(state)})
    session.modified = True
    return jsonify({"status": "moved", **public_state(state)})


def start_dungeon_encounter(state, marker):
    state["current_enemy_uid"] = marker["uid"]
    state["enemy"] = create_enemy(
        state["current_room"], elite=marker["elite"], relics=state["relics"], enemy_id=marker["enemy_id"]
    )
    state["pending"] = None
    if marker["elite"]:
        discover("mechanics", "elites")


@app.route("/api/dungeon/tick", methods=["POST"])
def tick_dungeon():
    state = session.get("game_state")
    if not state or state.get("pending") != "dungeon":
        return jsonify({"error": "The dungeon is not active."}), 400
    dungeon = state["dungeon"]
    for enemy in dungeon["enemies"]:
        if enemy["defeated"] or "BOSS" in enemy["kind"]:
            continue  # Boss waits at the center of its arena.
        if random.random() < .12:
            heading = random.random() * math.tau
            enemy["vx"], enemy["vy"] = math.cos(heading), math.sin(heading)
        x = enemy["x"] + enemy.get("vx", .5) * .16
        y = enemy["y"] + enemy.get("vy", .5) * .16
        if not walkable(dungeon, x, y, .35):
            enemy["vx"] = -enemy.get("vx", .5)
            enemy["vy"] = -enemy.get("vy", .5)
        else:
            enemy["x"], enemy["y"] = round(x, 3), round(y, 3)
        if math.hypot(enemy["x"] - dungeon["player"]["x"], enemy["y"] - dungeon["player"]["y"]) < .52:
            start_dungeon_encounter(state, enemy)
            session.modified = True
            return jsonify({"status": "encounter_started", **public_state(state)})
    session.modified = True
    return jsonify({"status": "roaming", **public_state(state)})


@app.route("/api/question", methods=["GET"])
def get_question():
    state = session.get("game_state")
    if not state or state.get("game_over") or not state.get("enemy") or state.get("pending"):
        return jsonify({"error": "No active combat question"}), 400
    question = current_question(state)
    tier = get_tier(state["current_room"])
    time_limit = 30 if "haste" in state["enemy"]["abilities"] else 45
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
    state.setdefault("focus", 0)
    user_answer = data.get("answer")
    is_timeout = data.get("timeout", False)
    combat_action = data.get("combat_action", "attack")
    if combat_action not in {"attack", "defend", "exploit"}:
        return jsonify({"error": "Choose Attack, Defend, or Exploit"}), 400
    if combat_action == "exploit" and state["focus"] < 2:
        return jsonify({"error": "Exploit requires 2 Focus. Use Attack to build it."}), 400
    state["answer_lock"] = 0
    state["answer_lock_source"] = None
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
    recovered_hp = 0
    if combat_action == "exploit":
        state["focus"] -= 2

    if is_correct:
        state["stats"]["correct_answers"] += 1
        state["combo"] += 1
        if combat_action == "attack":
            state["focus"] = min(2, state["focus"] + 1)
        if combat_action in {"attack", "exploit"}:
            base_damage = 2 if combat_action == "attack" else 4
            if state["combo"] % 3 == 0:
                base_damage += 2 if "exploit_chain" in state["relics"] else 1
            if question.get("domain") == "Linux" and "tux_kernel" in state["relics"]:
                base_damage += 1
            if question.get("domain") == "Web Security" and "web_proxy" in state["relics"]:
                base_damage += 1
            if state["effects"].get("root_lock"):
                base_damage = max(0, base_damage - 1)
                state["effects"]["root_lock"] = 0
            damage_dealt = base_damage
            armor_blocked = min(enemy.get("armor", 0), damage_dealt)
            damage_dealt -= armor_blocked
            enemy["armor"] = max(0, enemy.get("armor", 0) - armor_blocked)
            enemy["hp"] = max(0, enemy["hp"] - damage_dealt)
        credits_earned = 10 + (state["combo"] * 2) + (5 if "credit_miner" in state["relics"] else 0)
        state["credits"] += credits_earned
    else:
        state["combo"] = 0

    defeated_enemy = enemy["name"] if enemy["hp"] == 0 else None
    defeated_enemy_kind = enemy["kind"] if enemy["hp"] == 0 else None
    defeated_enemy_id = enemy["id"] if enemy["hp"] == 0 else None
    if enemy["hp"] == 0:
        hp_before_recovery = state["hp"]
        status = complete_combat(state)
        recovered_hp = state["hp"] - hp_before_recovery
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
        "defeated_enemy_kind": defeated_enemy_kind, "defeated_enemy_id": defeated_enemy_id,
        "recovered_hp": recovered_hp,
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
    if state.get("return_to_dungeon_after_reward"):
        return_to_dungeon(state)
    elif state.get("advance_after_reward"):
        advance_stage(state)
    else:
        return_to_stage_route(state)
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
    if state.get("dungeon"):
        return_to_dungeon(state)
    else:
        return_to_stage_route(state)
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
    if state.get("dungeon"):
        return_to_dungeon(state)
    else:
        return_to_stage_route(state)
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
    if state.get("dungeon"):
        return_to_dungeon(state)
    else:
        return_to_stage_route(state)
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
            result["defeated_enemy"] = enemy["name"]
            result["defeated_enemy_kind"] = enemy["kind"]
            result["defeated_enemy_id"] = enemy["id"]
            hp_before_recovery = state["hp"]
            result["status"] = complete_combat(state)
            result["recovered_hp"] = state["hp"] - hp_before_recovery
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
                    {"EASY": 3, "MEDIUM": 4, "HARD": 5}[tier]
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

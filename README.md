# Swinburne Cyber Dungeon

**Swinburne Cyber Dungeon** is a cybersecurity quiz roguelite built with
Python, Flask, HTML, CSS, and vanilla JavaScript.

The player travels through a procedurally varied 15-room run. Correct answers
damage enemies, wrong answers allow enemies to attack, and each route creates a
different combination of items, relics, shops, events, elites, and bosses.

The original *Swinburne Millionaire* project remains on the `main` branch.
The complete roguelite version is developed on `roguelike-v1`.

## Core game loop

1. Enter a combat room and answer cybersecurity questions.
2. Correct answers damage enemies and earn credits.
3. Wrong answers reset the combo and trigger enemy abilities.
4. Defeat the enemy and choose one reward.
5. Select one of two possible routes.
6. Improve the current build using consumables and relics.
7. Defeat the bosses in Rooms 5, 10, and 15.

Death ends the current run, but discovered encyclopedia entries and run
statistics remain available until the player resets all progress.

## Run structure

| Rooms | Area | Questions | Boss |
|---|---|---|---|
| 1–5 | Network Perimeter | Easy | Phishing King |
| 6–10 | Internal Network | Medium | Ransomware Overlord |
| 11–15 | Root Layer | Hard | The Root Admin |

The game contains 300 questions:

- `questions.json`: 100 Easy questions
- `questions_medium.json`: 100 Medium questions
- `questions_hard.json`: 100 Hard questions

## Room types

| Room | Purpose |
|---|---|
| Combat | Fight a normal enemy and receive loot |
| Elite | Fight a stronger multi-ability enemy for better rewards |
| Data Cache | Choose a consumable or credits |
| Repair Station | Restore HP or increase maximum HP |
| Dark Web Market | Spend credits on consumable items |
| Unknown Signal | Choose between event risks and rewards |
| Boss | Fight a fixed powerful enemy at Rooms 5, 10, and 15 |

Two random room choices are offered between required boss encounters.

## Consumable items

The inventory can hold four items. Consumables disappear after use.

| Item | Effect |
|---|---|
| Packet Sniffer | Removes two incorrect answers |
| Firewall | Blocks the next enemy attack |
| Health Patch | Restores 2 HP |
| Overclock | Adds 15 seconds to the current question |
| Sandbox | Prevents HP damage from the next wrong answer |
| Zero-Day | Immediately deals 2 enemy damage |
| Backup | Automatically revives the player with 1 HP |

Items can be used or discarded from the inventory bar. A full inventory must
be managed before another item can be collected.

## Relics

Relics provide passive effects for the remainder of the current run.

| Relic | Passive effect |
|---|---|
| Exploit Chain | Every third correct answer deals 3 damage |
| Tux Kernel | Correct Linux answers deal +1 damage |
| Wireshark | Networking questions receive 5 extra seconds |
| Web Proxy | Correct Web Security answers deal +1 damage |
| Zero Trust | Every fifth incoming attack is blocked |
| Root Access | Bosses begin with 1 HP already removed |
| Incident Response Plan | Restore 1 HP after defeating a boss |
| Credit Miner | Correct answers earn 5 additional credits |

Bosses always offer a choice of three relics. Elite enemies have a chance to
offer relics instead of normal loot.

## Enemy abilities

Enemies are no longer cosmetic. Their abilities change the rules of combat.

| Ability | Challenge |
|---|---|
| Hardened Shell | Reduces the first successful attack by 1 |
| Time Compression | Reduces the question timer to 20 seconds |
| Signal Jammer | Prevents Packet Sniffer use |
| Data Leech | Restores enemy HP after a wrong answer |
| Wallet Drain | Removes credits after a wrong answer |
| Encryption | Destroys a random inventory item after a wrong answer |
| Self Repair | Restores enemy HP after a wrong answer |
| Critical Strike | Deals one additional player damage |

Elite enemies combine two abilities. Bosses use fixed ability combinations.

## Bosses

| Room | Boss | HP | Abilities |
|---|---|---:|---|
| 5 | Phishing King | 4 | Signal Jammer |
| 10 | Ransomware Overlord | 6 | Encryption and Hardened Shell |
| 15 | The Root Admin | 8 | Time Compression and Self Repair |

The Root Admin also deals 2 damage with each successful attack.

## Encyclopedia and progression

The encyclopedia can be opened before a run or during gameplay. It records:

- mechanics
- room types
- consumable items
- relics
- enemies
- enemy abilities
- runs started, wins, and best room reached

Only discovered entries are visible. Undiscovered entries are displayed only
as locked totals, preventing the encyclopedia from spoiling future content.

Permanent progress also provides small milestones:

- After the first completed run, future runs begin with +1 maximum HP.
- From the third started run onward, runs begin with 50 credits.

The **Reset All Progress** option clears discoveries, statistics, milestone
bonuses, and any active run. A confirmation message is shown before deletion.

## Run summary

The end screen reports:

- answer accuracy
- enemies defeated
- total damage taken
- consumable items used
- final room and credits

## Run locally on Windows

Open the project folder in VS Code, then open **Terminal > New Terminal**:

```powershell
git switch roguelike-v1
git pull
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in a browser.

Press `Ctrl+C` in the terminal to stop the server.

## Automated checks

```powershell
python -m unittest -v
```

The automated suite checks combat, damage, combos, question difficulty,
question-bank integrity, rewards, routes, inventory, enemy abilities, boss
timers, encyclopedia locking, progress reset, and browser session size.

## Project structure

```text
app.py                    Flask routes, catalogues, combat and progression
questions.json            100 Easy questions
questions_medium.json     100 Medium questions
questions_hard.json       100 Hard questions
templates/index.html      Game interface and browser logic
static/style.css          Responsive roguelite design
static/*.mp3              Game audio
test_app.py               Automated game-system tests
```

## Technology

- Python 3
- Flask
- JavaScript
- HTML5
- CSS3
- Flask signed-cookie sessions for current-run and discovery progress

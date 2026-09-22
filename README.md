# Swinburne Cyber Dungeon

**Swinburne Cyber Dungeon** is a cybersecurity quiz roguelite built with
Python, Flask, HTML, CSS, and vanilla JavaScript.

The player fights through 15 combat stages. Every question is a combat turn:
choose Attack, Defend, or Exploit without knowing the enemy's next action, then
answer. Shops, repairs, caches, and events occur between fights and do not
advance the stage counter.

The original *Swinburne Millionaire* project remains on the `main` branch.
The complete roguelite version is developed on `roguelike-v1`.

## Core game loop

1. Choose Attack, Defend, or Exploit while the enemy action remains hidden.
2. Answer a concise cybersecurity question within 45 seconds.
3. Resolve both the player's action and the enemy's action.
4. Defeat the enemy and choose one reward.
5. Choose a combat path or take one optional support-room detour.
6. Improve the current build using consumables and relics.
7. Defeat the bosses at Stages 5, 10, and 15.

### Combat actions

| Action | Correct answer | Wrong answer |
|---|---|---|
| Attack | Deal 2 damage and gain 1 Focus; a surviving enemy always acts | Deal no damage; the enemy acts normally |
| Defend | Cancel the enemy action without building Focus | Reduce attack damage by 1; special actions still happen |
| Exploit | Spend 2 Focus to deal 4 damage and interrupt | Spend 2 Focus, deal no damage, and take +1 attack damage |

Enemy actions are revealed only after the turn resolves. Normal enemies have
3–5 HP, elites have 5–7 HP, and the player begins with 12 HP. Exploit is a
powerful finisher, but it must first be charged through Attack. Defend remains
the safe choice when survival matters, but cannot charge Exploit.

Powerful actions display a pulsing warning and play an alert sound without
revealing the exact move. A separate lethal warning appears when the incoming
attack could reduce the player to 0 HP. This gives Defend a clear tactical use
while keeping ordinary enemy turns unpredictable.

Every defeated enemy activates Combat Recovery and restores 1 HP. Additional
healing remains available from Health Patches, Repair Stations, Backup, and the
Incident Response Plan relic.

Death ends the current run, but discovered encyclopedia entries and run
statistics remain available until the player resets all progress.

## Run structure

| Stages | Area | Questions | Boss |
|---|---|---|---|
| 1–5 | Network Perimeter | Easy | Phishing King |
| 6–10 | Internal Network | Medium | Ransomware Overlord |
| 11–15 | Root Layer | Hard | The Root Admin |

The game contains 300 questions:

- `questions.json`: 100 Easy questions
- `questions_medium.json`: 100 Medium questions
- `questions_hard.json`: 100 Hard questions

All prompts are capped at 100 characters and every answer choice at 60
characters. Standard battles allow 45 seconds; Time Compression allows 30.

## Room types

| Room | Purpose |
|---|---|
| Combat | Fight a normal enemy and receive loot |
| Elite | Fight a stronger multi-ability enemy for better rewards |
| Data Cache | Choose a consumable or credits between stages |
| Repair Station | Restore or increase HP between stages |
| Dark Web Market | Spend credits between stages |
| Unknown Signal | Choose an event risk or reward between stages |
| Boss | Fight a fixed enemy at Stages 5, 10, and 15 |

Only defeated enemies advance the 15-stage run. After taking a support room,
the next route offers Combat and Elite choices so support rooms cannot be
farmed repeatedly or skip a boss.

## Consumable items

The inventory can hold four items. Consumables disappear after use.

| Item | Effect |
|---|---|
| Packet Sniffer | Removes two incorrect answers |
| Firewall | Blocks the next enemy attack |
| Health Patch | Restores 2 HP |
| Overclock | Adds 15 seconds to the current question |
| Sandbox | Blocks the next damaging enemy attack |
| Zero-Day | Immediately deals 2 enemy damage |
| Backup | Automatically revives the player with 1 HP |

Items can be used or discarded from the inventory bar. A full inventory must
be managed before another item can be collected.

## Relics

Relics provide passive effects for the remainder of the current run.

| Relic | Passive effect |
|---|---|
| Exploit Chain | Every third correct answer adds 2 damage instead of 1 |
| Tux Kernel | Correct Linux answers deal +1 damage |
| Wireshark | Networking questions receive 5 extra seconds |
| Web Proxy | Correct Web Security answers deal +1 damage |
| Zero Trust | Blocks the first damaging enemy attack in every battle |
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
| Time Compression | Reduces the question timer to 30 seconds |
| Signal Jammer | Can disable Packet Sniffer for two turns |
| Data Leech | Adds Self Repair to an enemy's turn pattern |
| Wallet Drain | Adds a turn that steals up to 20 credits |
| Encryption | Adds a turn that destroys a random inventory item |
| Self Repair | Adds a turn that restores 1 enemy HP |
| Critical Strike | Adds more Heavy Attacks to the turn pattern |

Enemy intent is hidden until the turn resolves. Enemy actions include
Attack, Heavy Attack, Fortify, Self Repair, Wallet Drain, Signal Jam, Encrypt,
and Root Lock. Elite enemies combine two abilities. Bosses change to a more
aggressive second pattern at half HP.

## Bosses

| Room | Boss | HP | Abilities |
|---|---|---:|---|
| 5 | Phishing King | 7 | Signal Jammer; phase-two Heavy Attacks |
| 10 | Ransomware Overlord | 10 | Encryption and Hardened Shell |
| 15 | The Root Admin | 14 | Time Compression, Self Repair, and Root Lock |

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

Only discovered entries are visible. Every unlocked card can be clicked to see
its full description and rules. Enemy pages also show HP, attack, abilities,
strategy, and phase-by-phase turn patterns. Undiscovered entries appear only as
locked totals, preventing the encyclopedia from spoiling future content.

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
- final stage and credits

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

The 28-test automated suite checks Focus requirements, hidden intentions,
danger and lethal warnings, post-fight healing, support-room stage rules,
question-length limits, all three combat actions, simultaneous damage, Zero
Trust, boss phases, combos, question difficulty,
question-bank integrity, rewards, routes, inventory, enemy abilities, boss
timers, encyclopedia detail data, progress reset, and browser session size.

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

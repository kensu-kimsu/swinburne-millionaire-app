# Swinburne Cyber Dungeon

**Swinburne Cyber Dungeon** is a cybersecurity adventure RPG dungeon crawler built with
Python, Flask, HTML, CSS, and vanilla JavaScript.

The player explores 15 illustrated open arenas with pointer and touch joystick movement. Each floor creates a distinct scene, random enemies, an
chance-based supply chest, and a locked exit. Touching a monster launches a
dedicated turn-based battle; every monster on the map must be defeated before
the gate to the next floor opens.

The original *Swinburne Millionaire* project remains on the `main` branch.
The complete roguelite version is developed on `roguelike-v1`.

## Core game loop

1. Explore an open illustrated arena by dragging the joystick with a mouse or finger.
2. Touch a roaming-map monster to enter its dedicated battle scene.
3. Choose Attack, Defend, or Exploit while the enemy action remains hidden.
4. Answer a concise cybersecurity question within 45 seconds.
5. Resolve both combatants' actions and return to the map; optional chests contain loot.
6. Defeat every enemy to unlock the exit and descend to the next floor.
7. Overcome the lone boss waiting in the center of Floors 5, 10, and 15.

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

Boss damage scales far beyond normal enemies: the Cyber Leviathan attacks for
2, Death Protocol for 3, and the Root Dragon for 4 before Heavy Attack bonuses.
Their signature spells can temporarily seal the answer grid while the question
timer continues, making boss warnings important even for expert players.

Powerful actions display a pulsing warning and play an alert sound without
revealing the exact move. A separate lethal warning appears when the incoming
attack could reduce the player to 0 HP. This gives Defend a clear tactical use
while keeping ordinary enemy turns unpredictable.

Combat now has a complete audiovisual feedback layer: animated enemy portraits
idle, lunge, recoil, and dissolve; Attack, Defend, Exploit, healing, and enemy
turns have distinct particles, flashes, motion, and sound cues. Sound playback
is centrally controlled, so warnings pause the dungeon pulse and starting a new
run immediately stops victory or defeat audio from the previous run.

The score adapts to the encounter: menu and exploration themes transition into
separate Easy, Medium, Hard, Elite, miniboss, major-boss, and final-boss music.
Every enemy technique has a distinct audio/visual signature, including fire and
impact for Heavy Attack, a shield dome for Fortify, green recovery particles,
gold drain spirals, jammer glitches, encryption shards, and a Root Lock vortex.
Exploit is presented as an ultimate attack with a beam, elemental detonation,
smoke, expanding rings, and a large particle burst.

On phones, exploration and combat each use a dedicated single-screen layout
sized with the dynamic mobile viewport. The dungeon has a virtual joystick,
enemy portraits are enlarged, answers remain in a legible two-by-two grid, and
items use a horizontal quick-access bar. Resolved-turn summaries open as a
fully opaque bottom sheet with their own scroll area, so the battlefield cannot
show through the text.

Answer, action, and reward selections provide immediate sound feedback. After a
turn resolves, the Continue button displays an eight-second countdown and advances
automatically if the player does not press it.

Combat summaries use color-coded highlights for the selected action, damage,
enemy skill, blocked damage, healing, boss phase changes, and credits earned so
the important result can be understood at a glance.

Every defeated enemy plays a victory fanfare. Floor bosses use a separate,
larger boss-victory fanfare, while the exploration and battle scores resume
only after the cue finishes.

Every defeated enemy activates Combat Recovery and restores 1 HP. Additional
healing remains available from Health Patches, Repair Stations, Backup, and the
Incident Response Plan relic.

Death ends the current run, but discovered encyclopedia entries and run
statistics remain available until the player resets all progress.

## Run structure

| Stages | Area | Questions | Boss |
|---|---|---|---|
| 1–5 | Network Perimeter | Easy | Cyber Leviathan |
| 6–10 | Internal Network | Medium | Death Protocol |
| 11–15 | Root Layer | Hard | The Root Dragon |

The game contains 300 questions:

- `questions.json`: 100 Easy questions
- `questions_medium.json`: 100 Medium questions
- `questions_hard.json`: 100 Hard questions

All prompts are capped at 100 characters and every answer choice at 60
characters. Standard battles allow 45 seconds; Time Compression allows 30.

## Dungeon floors and encounters

Each normal floor is a continuous illustrated arena with three roaming enemies.
Elite status is rolled independently at a 22% chance. Floors 5, 10, and 15
contain only the centered boss, with no ordinary monsters or support encounters.
The exit remains sealed until every encounter on the floor is defeated.

All fifteen levels have fixed obstacle layouts in an 18 by 11 world. A camera
follows the hero around the illustrated arena; obstacles stop the hero and roaming
enemies. Floors 1–5 use catacombs, 6–10 the temple, and 11–15 the foundry,
with special Atlantis, graveyard and inferno paintings on boss levels.
Painted ruins, volcanic rubble, and broken stalls mark the collidable obstacles.
Every exit has an animated magical portal set in front of a stone tunnel entrance;
it stays dim until the required enemies are defeated.

Supply chests appear on normal floors with a 38% chance and contain item or
relic choices. Battles award recovery, and dungeon loot is collected from chests.
After a cleared floor, a 30% chance opens a separate desolated market interlude.
The market has its own map and merchant near its exit; entering and leaving it
does not add to the fifteen-level counter. The merchant sells items for credits.

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
| Tidal Prison | Leviathan's Tsunami deals damage and submerges answers for 3 seconds |
| Petrification | Death Protocol seals answers for 5 seconds |
| Dragon Inferno | Root Meteor deals 6 base damage and scorches answers for 3 seconds |
| Time Stop | The Root Dragon seals answers for 6 seconds while the timer runs |

Enemy intent is hidden until the turn resolves. Enemy actions include
Attack, Heavy Attack, Fortify, Self Repair, Wallet Drain, Signal Jam, Encrypt,
Tsunami, Petrifying Gaze, Root Meteor, and Time Stop. Elite enemies combine two
abilities. Bosses change to a more aggressive second pattern at half HP. Every
monster family has its own attack palette and particle treatment; boss spells
add bespoke wave, stone, meteor, and frozen-time cinematics.

## Bosses

| Floor | Boss | HP | Abilities |
|---|---|---:|---|
| 5 | Cyber Leviathan | 7 | Abyssal Tsunami, Tidal Prison, Signal Jammer |
| 10 | Death Protocol | 10 | Petrifying Gaze, Encryption, Hardened Shell |
| 15 | The Root Dragon | 14 | Root Meteor, Time Stop, Time Compression, Self Repair |

The Root Dragon deals 4 normal damage; Root Meteor deals 6 before defences.

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

The 35-test automated suite checks procedural map creation, map collision,
locked exits, battle-to-map return, Focus requirements, hidden intentions,
danger and lethal warnings, post-fight healing, support encounter rules,
question-length limits, all three combat actions, simultaneous damage, Zero
Trust, boss phases, combos, question difficulty,
question-bank integrity, rewards, routes, inventory, enemy abilities, boss
timers, random elite ambushes, boss crowd-control spells, encyclopedia detail
data, progress reset, browser session size, and the custom audiovisual asset
bundle.

## Project structure

```text
app.py                    Flask routes, authored dungeon layouts, combat and progression
questions.json            100 Easy questions
questions_medium.json     100 Medium questions
questions_hard.json       100 Hard questions
templates/index.html      Game interface and browser logic
static/style.css          Responsive exploration and battle design
static/assets/audio/      Original generated adventure sound set
static/assets/backgrounds/ Illustrated cyber-dungeon menu backdrop
static/assets/enemies/    Illustrated animated enemy character artwork
static/assets/npcs/       Shopkeeper and future non-player characters
static/assets/ui/         Custom enemy, item, relic, room, and menu symbols
scripts/generate_soundscape.py  Rebuild the original WAV sound set
test_app.py               Automated game-system tests
```

## Art and audio

The interface uses a custom cyber-fantasy visual language rather than emoji
placeholders. Every enemy has a distinct illustrated fantasy species and
silhouette fused with cyber technology—from goblins, scarabs, golems, panthers,
ogres, liches, and werewolves to a hydra, leviathan, reaper, and final dragon.
Elite encounters receive a separate ultraviolet corruption palette and aura.
The SVG
atlas contains every consumable and relic, room symbols, combat actions, menu
marks, and encyclopedia artwork. CSS motion keeps these assets animated without
requiring video downloads.

All music cues and sound effects are original, dependency-free synthesized
audio generated specifically for the game. To rebuild them:

```powershell
python scripts/generate_soundscape.py
```

This recreates the adaptive music suite, dungeon pulse, warnings, attacks,
individual enemy skills, defend and exploit cues, healing, loot, selection and
confirmation feedback, victory, defeat, and answer feedback sounds.

## Technology

- Python 3
- Flask
- JavaScript
- HTML5
- CSS3
- Flask signed-cookie sessions for current-run and discovery progress

## Illustrated exploration

The hero moves with a touch or mouse joystick and desktop directional keys.
A camera follows free movement across each of fifteen authored maps; there is
no visible tile grid. Environmental fire, mist, runes and sparks animate while
enemies wander and switch between individual idle and moving frames. The enemy
sheets are split into four standalone images each to prevent the browser from
drawing several poses at once. The battle portrait uses the same illustrated
frame as the map actor. A movement reminder fades in after 20 seconds
without input. Bosses wait alone at the center of their arenas with particle
auras. Combat retains readable turn summaries, victory music, and a distinct
boss fanfare.

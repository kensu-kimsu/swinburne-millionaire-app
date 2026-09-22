# Swinburne Cyber Dungeon

A cybersecurity quiz roguelike made with Python, Flask, HTML, CSS and vanilla
JavaScript.

This branch changes the original *Swinburne Millionaire* school project into a
combat-based quiz game. The original version remains safe on the `main` branch.

## Version 1 features

- A 15-room run with easy, medium and hard areas
- Three difficulty-matched question banks with 100 questions each
- Five player health points
- Correct answers damage enemies
- Wrong answers and timeouts damage the player
- A combo system that deals two damage on every third correct answer
- Credits earned from correct answers
- A reusable room-path interface
- The Packet Sniffer power-up, which removes two wrong answers
- A miniboss in room 5
- A major boss in room 10
- A final boss in room 15

## Bosses

| Room | Boss | Health | Damage |
|---|---|---:|---:|
| 5 | Phishing King | 3 | 1 |
| 10 | Ransomware Overlord | 4 | 1 |
| 15 | The Root Admin | 5 | 2 |

## Run the game on Windows

Open the project folder in VS Code. Then open **Terminal > New Terminal** and
enter these commands one at a time:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in your browser.

To stop the server, return to the terminal and press `Ctrl+C`.

## Run the automated checks

With the virtual environment activated, run:

```powershell
python -m unittest -v
```

The five tests check the starting health, damage from a wrong answer, normal
room progression, combo damage and final-boss victory.

## Beginner Git workflow

See which branch you are using and which files changed:

```powershell
git status
```

Move to the roguelike branch:

```powershell
git switch roguelike-v1
```

Upload the branch to GitHub for the first time:

```powershell
git push -u origin roguelike-v1
```

After the first upload, future saved commits only need:

```powershell
git push
```

## Project files

```text
app.py                   Flask routes and game rules
questions.json            100 Easy cybersecurity questions
questions_medium.json     100 Medium cybersecurity questions
questions_hard.json       100 Hard cybersecurity questions
templates/index.html  Page structure and browser game logic
static/style.css      Roguelike visual design
test_app.py           Automated game-rule checks
```

## Planned versions

1. **Version 1 — Combat foundation:** HP, enemies, combos and bosses
2. **Version 2 — Loot:** choose one of three rewards after boss fights
3. **Version 3 — Inventory:** Firewall, Health Patch and Overclock
4. **Version 4 — Relics and shops:** passive builds and credit spending
5. **Version 5 — Random events and branching paths**

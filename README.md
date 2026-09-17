# 🏆 Swinburne Millionaire

**Swinburne Millionaire** is an interactive, web-based cybersecurity and IT trivia game modeled after the classic *"Who Wants to Be a Millionaire?"* show format[cite: 2, 3]. Built with **Python (Flask)** and vanilla **JavaScript/CSS3**, it tests technical cybersecurity knowledge across 15 dynamic difficulty tiers[cite: 2].

---

## 📸 Application Screenshots

| Title Screen | Active Gameplay |
| :---: | :---: |
| ![Title Screen](screenshots/title-screen.png) | ![Gameplay Screen](screenshots/gameplay.png) |

| Checkpoint | Game Over Screen |
| :---: | :---: |
| ![Checkpoint Modal](screenshots/checkpoint-modal.png) | ![Game Over Screen](screenshots/gameover-screen.png) |

---

## 🎮 How the Game Works

The objective of the game is simple: answer 15 consecutive cybersecurity questions correctly to win the top prize of **$1,000,000**[cite: 2, 3].

### 1. Game Flow & Rule Mechanics
* **15 Question Tiers:** Questions increase in difficulty as you advance through three main tiers: **EASY** (Q1–Q5), **MEDIUM** (Q6–Q10), and **HARD** (Q11–Q15)[cite: 2].
* **30-Second Countdown Timer:** Every question gives you 30 seconds to lock in an answer[cite: 2, 3]. If the timer reaches zero before you choose, the game ends immediately[cite: 2, 3].
* **Lock-In Mechanism:** Clicking an option highlights your choice[cite: 3]. You must click **FINAL ANSWER** to submit your option[cite: 3].
* **Instant Feedback & Explanations:** After submitting an answer, the game highlights whether you were correct (green) or wrong (red) and displays a detailed technical explanation for why that option was right or wrong[cite: 3].

---

## 🛡️ Lifelines & Safety Checkpoints

### 💡 50:50 Lifeline
* Accessible once per game session[cite: 2].
* Uses the server API to randomly eliminate **two incorrect choices**, leaving only the correct answer and one wrong distraction[cite: 2].

### 💰 Safe Checkpoints ($1,000 & $32,000)
When you successfully answer Question 5 ($1,000) or Question 10 ($32,000), you unlock a **Safe Milestone**[cite: 2, 3]:
* **Risk & Continue:** Proceed to harder questions while guaranteeing you won't leave empty-handed if you miss a future question[cite: 2, 3].
* **Walk Away / Cash Out:** Choose to leave the game at any point before answering a question to lock in your current earnings[cite: 2, 3].

---

## 🎭 Interactive Audio & Dynamic Events

* **Spotlights & Particle Animations:** Custom HTML5 canvas routines trigger background glitter effects upon winning and red spotlights when starting games[cite: 3, 4].
* **Dynamic Audio Engine:** Contextual audio plays during ticks, lock-ins, safe choices, lifelines, game-over moments, and full victories[cite: 3].
* **Roast & Insult System:** If you run out of time or select a wrong option, the app dynamically assigns humorous cybersecurity-themed insults alongside custom falling emoji animations[cite: 2, 4].

---

## ⚡ Tech Stack Summary

* **Backend Engine:** Python 3.11+, Flask Web Framework (Session-based state management)[cite: 2]
* **Frontend Design:** HTML5, CSS3, Vanilla ES6 JavaScript[cite: 3, 4]
* **Media Handling:** HTML5 Audio API & HTML5 Canvas Rendering[cite: 3, 4]

import unittest
from pathlib import Path
from unittest.mock import patch

from app import app, create_enemy, load_questions


class RoguelikeGameTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()
        self.client.post("/api/start")
        # Most combat unit tests enter a direct isolated encounter. Dedicated
        # dungeon-flow tests below exercise the exploration layer end to end.
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["dungeon"] = None
            state["pending"] = None
            state["enemy"] = create_enemy(1)
            state["current_enemy_uid"] = None
            flask_session["game_state"] = state
            progress = flask_session["meta_progress"]
            if state["enemy"]["id"] not in progress["unlocked_enemies"]:
                progress["unlocked_enemies"].append(state["enemy"]["id"])
            for ability in state["enemy"]["abilities"]:
                if ability not in progress["unlocked_abilities"]:
                    progress["unlocked_abilities"].append(ability)
            flask_session["meta_progress"] = progress

    def answer_for_current_question(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            if state["current_room"] <= 5:
                tier = "EASY"
            elif state["current_room"] <= 10:
                tier = "MEDIUM"
            else:
                tier = "HARD"
            position = state["question_positions"][tier]
            question_index = state["question_orders"][tier][position]
        return load_questions(tier)[question_index]["answer"]

    def test_new_run_starts_with_twelve_hp_and_hidden_intent(self):
        response = self.client.get("/api/question")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["room"], 1)
        self.assertEqual(data["hp"], 12)
        self.assertEqual(data["enemy"]["hp"], 3)
        self.assertTrue(data["enemy"]["intent_hidden"])
        self.assertNotIn("intent", data["enemy"])
        self.assertNotIn("intent_detail", data["enemy"])

    def test_session_cookie_stays_within_browser_limit(self):
        response = self.client.post("/api/start")
        cookie = response.headers.get("Set-Cookie", "")
        self.assertLess(len(cookie), 4093)

    def test_new_run_opens_a_random_dungeon_floor(self):
        data = self.client.post("/api/start").get_json()

        self.assertEqual(data["pending"], "dungeon")
        self.assertIsNone(data["enemy"])
        self.assertEqual(data["dungeon"]["width"], 9)
        self.assertEqual(data["dungeon"]["height"], 7)
        self.assertEqual(data["dungeon"]["remaining"], 3)
        self.assertNotIn("tiles", data["dungeon"])
        self.assertFalse(data["dungeon"]["exit_unlocked"])

    def test_touching_a_dungeon_enemy_starts_its_battle(self):
        self.client.post("/api/start")
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            marker = state["dungeon"]["enemies"][0]
            marker.update({"x": 1.4, "y": 3, "enemy_id": "spam_bot", "elite": False})
            state["dungeon"]["player"] = {"x": 1, "y": 3}
            for other in state["dungeon"]["enemies"][1:]: other["defeated"] = True
            flask_session["game_state"] = state

        data = self.client.post("/api/dungeon/move", json={"x": 1.1, "y": 3}).get_json()

        self.assertEqual(data["status"], "encounter_started")
        self.assertEqual(data["enemy"]["id"], "spam_bot")
        self.assertIsNone(data["pending"])

    def test_roaming_enemy_can_enter_player_tile_and_start_battle(self):
        self.client.post("/api/start")
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            dungeon = state["dungeon"]
            dungeon["player"] = {"x": 1, "y": 3}
            dungeon["enemies"][0].update({"x": 1.56, "y": 3, "vx": -1, "vy": 0, "enemy_id": "spam_bot", "elite": False})
            for other in dungeon["enemies"][1:]: other["defeated"] = True
            flask_session["game_state"] = state
        with patch("app.random.random", return_value=1):
            data = self.client.post("/api/dungeon/tick").get_json()
        self.assertEqual(data["status"], "encounter_started")
        self.assertEqual(data["enemy"]["id"], "spam_bot")

    def test_illustrated_arenas_and_joystick_assets_are_available(self):
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="movement-stick"', page)
        self.assertIn("requestAnimationFrame(movementFrame)", page)
        for name in ("hero-illustrated", "stage-catacomb", "stage-atlantis", "stage-graveyard",
                     "stage-inferno", "boss-leviathan", "boss-death", "boss-dragon"):
            self.assertGreater((Path(__file__).parent / "static/assets/dungeon" / f"{name}.webp").stat().st_size, 1000)
        for enemy in ("spam_bot", "phishing_email", "adware_bug", "botnet_node", "credential_thief",
                      "malware_loader", "ransomware", "insider_threat", "zero_day_exploit"):
            self.assertGreater((Path(__file__).parent / "static/assets/dungeon" / f"run-{enemy}.webp").stat().st_size, 1000)

    def test_boss_arena_has_only_the_centered_boss(self):
        from app import create_dungeon_floor
        for stage, theme, boss in ((5, "atlantis", "phishing_king"),
                                   (10, "graveyard", "ransomware_overlord"),
                                   (15, "inferno", "root_admin")):
            with self.client.session_transaction() as flask_session:
                state = flask_session["game_state"]
                state["current_room"] = stage
                create_dungeon_floor(state)
                flask_session["game_state"] = state
            dungeon = self.client.get("/api/state").get_json()["dungeon"]
            self.assertEqual(dungeon["theme"], theme)
            self.assertEqual(len(dungeon["enemies"]), 1)
            self.assertEqual(dungeon["enemies"][0]["enemy_id"], boss)
            self.assertEqual((dungeon["enemies"][0]["x"], dungeon["enemies"][0]["y"]), (4.5, 3.35))
            self.assertIsNone(dungeon["feature"])

    def test_open_arena_movement_is_continuous_and_bounded(self):
        self.client.post("/api/start")
        before = self.client.get("/api/state").get_json()["dungeon"]["player"]
        moved = self.client.post("/api/dungeon/move", json={"x": before["x"] + .16, "y": before["y"] + .12}).get_json()
        self.assertAlmostEqual(moved["dungeon"]["player"]["x"], before["x"] + .16)
        self.assertAlmostEqual(moved["dungeon"]["player"]["y"], before["y"] + .12)
        self.assertEqual(self.client.post("/api/dungeon/move", json={"x": "NaN", "y": 2}).status_code, 400)

    def test_dungeon_exit_requires_every_enemy_and_advances_floor(self):
        self.client.post("/api/start")
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["dungeon"]["player"] = {"x": 1, "y": 3}
            state["dungeon"]["exit"] = {"x": 1.4, "y": 3}
            for enemy in state["dungeon"]["enemies"]: enemy.update({"x": 7, "y": 5})
            flask_session["game_state"] = state
        locked = self.client.post("/api/dungeon/move", json={"x": 1.1, "y": 3}).get_json()
        self.assertEqual(locked["status"], "exit_locked")

        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["dungeon"]["player"] = {"x": 1, "y": 3}
            for enemy in state["dungeon"]["enemies"]:
                enemy["defeated"] = True
            flask_session["game_state"] = state
        advanced = self.client.post("/api/dungeon/move", json={"x": 1.1, "y": 3}).get_json()

        self.assertEqual(advanced["status"], "floor_advanced")
        self.assertEqual(advanced["room"], 2)
        self.assertEqual(advanced["pending"], "dungeon")

    def test_dungeon_victory_reward_returns_to_the_same_floor(self):
        self.client.post("/api/start")
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            marker = state["dungeon"]["enemies"][0]
            marker.update({"x": 1.4, "y": 3, "enemy_id": "spam_bot", "elite": False})
            state["dungeon"]["player"] = {"x": 1, "y": 3}
            for other in state["dungeon"]["enemies"][1:]: other.update({"x": 7, "y": 5})
            flask_session["game_state"] = state

        encounter = self.client.post("/api/dungeon/move", json={"x": 1.1, "y": 3}).get_json()
        self.assertEqual(encounter["status"], "encounter_started")
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"]["hp"] = 1
            flask_session["game_state"] = state

        defeated = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "attack"},
        ).get_json()
        self.assertEqual(defeated["status"], "enemy_defeated")
        self.assertEqual(defeated["pending"], "reward")
        reward = next(entry for entry in defeated["reward_options"] if entry["type"] == "credits")
        returned = self.client.post(
            "/api/reward/choose", json={"reward_id": reward["id"]}
        ).get_json()

        self.assertEqual(returned["pending"], "dungeon")
        self.assertEqual(returned["room"], 1)
        self.assertEqual(returned["dungeon"]["remaining"], 2)
        self.assertTrue(returned["dungeon"]["enemies"][0]["defeated"])

    def test_wrong_answer_removes_hp_but_run_continues(self):
        correct_answer = self.answer_for_current_question()
        wrong_answer = next(key for key in "ABCD" if key != correct_answer)

        response = self.client.post("/api/answer", json={"answer": wrong_answer})
        data = response.get_json()

        self.assertEqual(data["status"], "player_hit")
        self.assertEqual(data["hp"], 11)
        self.assertEqual(data["room"], 1)

    def test_correct_answer_clears_a_normal_room(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"]["hp"] = 1
            flask_session["game_state"] = state
        response = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question()},
        )
        data = response.get_json()

        self.assertEqual(data["status"], "enemy_defeated")
        self.assertEqual(data["pending"], "reward")
        self.assertEqual(data["room"], 1)
        self.assertGreater(data["credits"], 0)

    def test_every_third_combo_deals_two_damage(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["current_room"] = 5
            state["enemy"] = create_enemy(5)
            state["combo"] = 2
            flask_session["game_state"] = state

        response = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question()},
        )
        data = response.get_json()

        self.assertEqual(data["damage_dealt"], 3)
        self.assertEqual(data["enemy"]["hp"], 4)

    def test_defeating_final_boss_wins_the_run(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["current_room"] = 15
            state["enemy"] = create_enemy(15)
            state["enemy"]["hp"] = 1
            flask_session["game_state"] = state

        response = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question()},
        )
        data = response.get_json()

        self.assertEqual(data["status"], "won")
        self.assertIsNone(data["enemy"])
        self.assertEqual(data["pending"], "complete")

    def test_rooms_use_the_correct_difficulty_bank(self):
        expected_tiers = [(1, "EASY"), (6, "MEDIUM"), (11, "HARD")]

        for room, expected_tier in expected_tiers:
            with self.client.session_transaction() as flask_session:
                state = flask_session["game_state"]
                state["current_room"] = room
                state["enemy"] = create_enemy(room)
                flask_session["game_state"] = state

            response = self.client.get("/api/question")
            data = response.get_json()

            self.assertEqual(data["tier"], expected_tier)

    def test_question_banks_are_complete_and_valid(self):
        expected_counts = {"EASY": 100, "MEDIUM": 100, "HARD": 100}
        all_ids = set()

        for tier, expected_count in expected_counts.items():
            questions = load_questions(tier)
            self.assertEqual(len(questions), expected_count)

            for question in questions:
                self.assertEqual(set(question["options"]), {"A", "B", "C", "D"})
                self.assertIn(question["answer"], question["options"])
                self.assertTrue(question["question"].strip())
                self.assertTrue(question["explanation"].strip())
                self.assertLessEqual(len(question["question"]), 100)
                self.assertLessEqual(max(map(len, question["options"].values())), 60)

                question_id = str(question["id"])
                unique_id = f"{tier}-{question_id}"
                self.assertNotIn(unique_id, all_ids)
                all_ids.add(unique_id)

    def test_reward_then_route_choice_advances_the_run(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"]["hp"] = 1
            flask_session["game_state"] = state
        answer = self.answer_for_current_question()
        defeated = self.client.post("/api/answer", json={"answer": answer}).get_json()
        credit_reward = next(
            reward for reward in defeated["reward_options"]
            if reward["type"] == "credits"
        )

        rewarded = self.client.post(
            "/api/reward/choose",
            json={"reward_id": credit_reward["id"]},
        ).get_json()

        self.assertEqual(rewarded["room"], 2)
        self.assertEqual(rewarded["pending"], "route")
        room_type = rewarded["room_options"][0]["id"]
        selected = self.client.post(
            "/api/route/choose",
            json={"room_type": room_type},
        )
        self.assertEqual(selected.status_code, 200)

    def test_room_four_reward_transitions_into_boss_question(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["current_room"] = 4
            state["enemy"] = create_enemy(4)
            state["enemy"]["hp"] = 1
            flask_session["game_state"] = state

        defeated = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question()},
        ).get_json()
        reward = next(
            entry for entry in defeated["reward_options"]
            if entry["type"] == "credits"
        )
        boss_state = self.client.post(
            "/api/reward/choose",
            json={"reward_id": reward["id"]},
        ).get_json()

        self.assertEqual(boss_state["room"], 5)
        self.assertIsNone(boss_state["pending"])
        self.assertEqual(boss_state["enemy"]["id"], "phishing_king")
        self.assertEqual(boss_state["enemy"]["name"], "Cyber Leviathan")
        self.assertEqual(self.client.get("/api/question").status_code, 200)

    def test_boss_timeout_returns_to_a_valid_question(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["current_room"] = 5
            state["enemy"] = create_enemy(5)
            flask_session["game_state"] = state

        timed_out = self.client.post("/api/answer", json={"timeout": True})
        self.assertEqual(timed_out.status_code, 200)
        self.assertEqual(timed_out.get_json()["status"], "player_hit")
        self.assertEqual(self.client.get("/api/question").status_code, 200)

    def test_firewall_blocks_the_next_wrong_answer(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["inventory"].append("firewall")
            flask_session["game_state"] = state

        used = self.client.post("/api/item/use", json={"item_id": "firewall"})
        self.assertEqual(used.get_json()["effects"]["firewall"], 1)
        correct_answer = self.answer_for_current_question()
        wrong_answer = next(key for key in "ABCD" if key != correct_answer)
        result = self.client.post("/api/answer", json={"answer": wrong_answer}).get_json()

        self.assertEqual(result["damage_taken"], 0)
        self.assertEqual(result["blocked_by"], "Firewall")
        self.assertEqual(result["hp"], 12)

    def test_ransomware_encryption_destroys_an_inventory_item(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["current_room"] = 10
            state["enemy"] = create_enemy(10)
            state["enemy"]["intent"] = "encrypt"
            state["inventory"] = ["firewall", "health_patch"]
            flask_session["game_state"] = state

        correct_answer = self.answer_for_current_question()
        wrong_answer = next(key for key in "ABCD" if key != correct_answer)
        with patch("app.random.randrange", return_value=0):
            result = self.client.post("/api/answer", json={"answer": wrong_answer}).get_json()

        self.assertEqual(result["destroyed_item"]["id"], "firewall")
        self.assertEqual(len(result["inventory"]), 1)

    def test_attack_damages_both_sides_when_enemy_survives(self):
        result = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "attack"},
        ).get_json()

        self.assertTrue(result["is_correct"])
        self.assertEqual(result["damage_dealt"], 2)
        self.assertEqual(result["damage_taken"], 1)
        self.assertEqual(result["hp"], 11)
        self.assertEqual(result["enemy"]["hp"], 1)
        self.assertEqual(result["focus"], 1)

    def test_correct_defend_interrupts_enemy_intent(self):
        result = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "defend"},
        ).get_json()

        self.assertEqual(result["damage_dealt"], 0)
        self.assertEqual(result["damage_taken"], 0)
        self.assertTrue(result["enemy_action"]["canceled"])
        self.assertEqual(result["hp"], 12)
        self.assertEqual(result["focus"], 0)

    def test_correct_exploit_deals_double_damage_and_interrupts(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"]["hp"] = 5
            state["enemy"]["max_hp"] = 5
            state["focus"] = 2
            flask_session["game_state"] = state

        result = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "exploit"},
        ).get_json()

        self.assertEqual(result["damage_dealt"], 4)
        self.assertEqual(result["damage_taken"], 0)
        self.assertTrue(result["enemy_action"]["canceled"])
        self.assertEqual(result["enemy"]["hp"], 1)

    def test_wrong_exploit_increases_incoming_attack(self):
        correct = self.answer_for_current_question()
        wrong = next(key for key in "ABCD" if key != correct)
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["focus"] = 2
            flask_session["game_state"] = state
        result = self.client.post(
            "/api/answer", json={"answer": wrong, "combat_action": "exploit"}
        ).get_json()

        self.assertEqual(result["damage_taken"], 2)
        self.assertEqual(result["hp"], 10)

    def test_zero_trust_blocks_only_first_damaging_attack_in_battle(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["relics"] = ["zero_trust"]
            state["enemy"]["hp"] = 6
            state["enemy"]["max_hp"] = 6
            state["enemy"]["intent"] = "heavy_attack"
            flask_session["game_state"] = state

        first = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "attack"},
        ).get_json()
        self.assertEqual(first["blocked_by"], "Zero Trust")
        self.assertEqual(first["hp"], 12)

        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"]["intent"] = "heavy_attack"
            flask_session["game_state"] = state
        second = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "attack"},
        ).get_json()
        self.assertIsNone(second["blocked_by"])
        self.assertEqual(second["hp"], 10)

    def test_threat_warning_telegraphs_danger_without_revealing_move(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"]["intent"] = "heavy_attack"
            flask_session["game_state"] = state

        data = self.client.get("/api/question").get_json()

        self.assertEqual(data["threat_warning"]["level"], "danger")
        self.assertNotIn("intent", data["enemy"])

    def test_threat_warning_marks_potentially_fatal_attack(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["hp"] = 2
            state["enemy"]["intent"] = "heavy_attack"
            flask_session["game_state"] = state

        data = self.client.get("/api/question").get_json()
        self.assertEqual(data["threat_warning"]["level"], "fatal")

    def test_defeating_enemy_restores_one_hp(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["hp"] = 10
            state["enemy"]["hp"] = 1
            flask_session["game_state"] = state

        result = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "attack"},
        ).get_json()

        self.assertEqual(result["status"], "enemy_defeated")
        self.assertEqual(result["recovered_hp"], 1)
        self.assertEqual(result["hp"], 11)

    def test_exploit_requires_two_focus(self):
        response = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "exploit"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("2 Focus", response.get_json()["error"])

    def test_support_room_does_not_advance_stage(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"] = None
            state["pending"] = "route"
            state["room_options"] = ["heal", "combat"]
            flask_session["game_state"] = state

        selected = self.client.post("/api/route/choose", json={"room_type": "heal"}).get_json()
        self.assertEqual(selected["room"], 1)
        repaired = self.client.post("/api/heal/choose", json={"choice": "repair"}).get_json()

        self.assertEqual(repaired["room"], 1)
        self.assertEqual(repaired["pending"], "route")
        self.assertEqual([entry["id"] for entry in repaired["room_options"]], ["combat"])

    def test_elite_enemy_is_a_random_combat_ambush(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"] = None
            state["pending"] = "route"
            state["room_options"] = ["combat"]
            flask_session["game_state"] = state

        with patch("app.random.random", return_value=0.0):
            result = self.client.post("/api/route/choose", json={"room_type": "combat"}).get_json()

        self.assertEqual(result["enemy"]["kind"], "ELITE")
        self.assertEqual(result["enemy"]["attack"], 2)

    def test_boss_spells_lock_the_next_answer_grid(self):
        cases = [
            (5, "tsunami", 2, 3),
            (10, "petrify", 0, 5),
            (15, "meteor", 6, 3),
            (15, "time_stop", 0, 6),
        ]
        for room, intent, expected_damage, expected_lock in cases:
            self.client.post("/api/start")
            with self.client.session_transaction() as flask_session:
                state = flask_session["game_state"]
                state["current_room"] = room
                state["enemy"] = create_enemy(room)
                state["enemy"]["intent"] = intent
                state["pending"] = None
                state["dungeon"] = None
                flask_session["game_state"] = state
            correct = self.answer_for_current_question()
            wrong = next(key for key in "ABCD" if key != correct)
            result = self.client.post("/api/answer", json={"answer": wrong}).get_json()

            self.assertEqual(result["damage_taken"], expected_damage)
            self.assertEqual(result["enemy_action"]["answer_lock_seconds"], expected_lock)
            self.assertEqual(self.client.get("/api/question").get_json()["answer_lock"], expected_lock)

    def test_boss_enters_phase_two_at_half_hp(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["current_room"] = 5
            state["enemy"] = create_enemy(5)
            state["enemy"]["hp"] = 4
            flask_session["game_state"] = state

        result = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "attack"},
        ).get_json()

        self.assertTrue(result["phase_changed"])
        self.assertEqual(result["enemy"]["phase"], 2)

    def test_encyclopedia_enemy_has_clickable_detail_data(self):
        data = self.client.get("/api/encyclopedia").get_json()
        enemy = data["enemies"][0]

        self.assertTrue(enemy["description"])
        self.assertTrue(enemy["strategy"])
        self.assertTrue(enemy["patterns"][0])
        self.assertIn("name", enemy["patterns"][0][0])

    def test_final_boss_uses_shorter_timer(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["current_room"] = 15
            state["enemy"] = create_enemy(15)
            flask_session["game_state"] = state

        data = self.client.get("/api/question").get_json()
        self.assertEqual(data["time_limit"], 30)

    def test_encyclopedia_only_returns_discovered_content(self):
        data = self.client.get("/api/encyclopedia").get_json()
        enemy_ids = {enemy["id"] for enemy in data["enemies"]}

        self.assertTrue(enemy_ids)
        self.assertGreater(data["locked_counts"]["enemies"], 0)
        self.assertNotIn("root_admin", enemy_ids)

    def test_progress_can_be_completely_reset(self):
        self.client.post("/api/start")
        response = self.client.post("/api/progress/reset")
        self.assertEqual(response.get_json()["status"], "progress_reset")

        encyclopedia = self.client.get("/api/encyclopedia").get_json()
        self.assertEqual(encyclopedia["progress"]["runs_started"], 0)
        self.assertEqual(encyclopedia["progress"]["best_room"], 0)

    def test_custom_art_and_sound_assets_are_available(self):
        project_root = Path(__file__).parent
        page = self.client.get("/").get_data(as_text=True)
        expected_assets = [
            "assets/backgrounds/cyber-dungeon.webp",
            "assets/ui/game-icons.svg",
            "assets/audio/dungeon_pulse.wav",
            "assets/audio/player_attack.wav",
            "assets/audio/enemy_attack.wav",
            "assets/audio/ui_select.wav",
            "assets/audio/skill_root_lock.wav",
            "assets/audio/music_menu.wav",
            "assets/audio/music_easy.wav",
            "assets/audio/music_final_boss.wav",
            "assets/audio/music_shop.wav",
            "assets/audio/shop_open.wav",
            "assets/audio/shop_buy.wav",
            "assets/audio/major_boss_victory.wav",
            "assets/audio/victory.wav",
            "assets/audio/defeat.wav",
        ]
        for asset in expected_assets:
            self.assertIn(asset, page if asset != "assets/backgrounds/cyber-dungeon.webp" else (project_root / "static/style.css").read_text())
            path = project_root / "static" / asset.removeprefix("assets/")
            if asset.startswith("assets/"):
                path = project_root / "static" / asset
            self.assertTrue(path.is_file(), asset)
            self.assertGreater(path.stat().st_size, 100, asset)
        stylesheet = (project_root / "static/style.css").read_text()
        self.assertIn("height: 100dvh", stylesheet)
        self.assertIn('id="mobile-current-room"', page)
        self.assertIn('id="ui-credits"', (project_root / "static/assets/ui/game-icons.svg").read_text())
        self.assertIn("beginAutoContinue()", page)
        self.assertIn("const delaySeconds = 8", page)
        self.assertIn("CIPHER'S RELIC EMPORIUM", page)
        self.assertIn("card.classList.toggle('elite'", page)
        self.assertIn("applyAnswerLock(data.answer_lock", page)
        self.assertIn("skill-tsunami", stylesheet)
        self.assertIn("skill-meteor", stylesheet)
        self.assertIn("answer-lock-overlay", stylesheet)
        self.assertIn(".enemy-card.elite", stylesheet)
        self.assertEqual(create_enemy(10)["name"], "Death Protocol")
        self.assertEqual(create_enemy(15)["name"], "The Root Dragon")
        for enemy_id in (
            "spam_bot", "phishing_email", "adware_bug", "botnet_node",
            "credential_thief", "malware_loader", "ransomware",
            "insider_threat", "zero_day_exploit", "phishing_king",
            "ransomware_overlord", "root_admin",
        ):
            self.assertTrue((project_root / "static/assets/enemies" / f"{enemy_id}.webp").is_file())
        self.assertTrue((project_root / "static/assets/npcs/cipher_merchant.webp").is_file())


if __name__ == "__main__":
    unittest.main()

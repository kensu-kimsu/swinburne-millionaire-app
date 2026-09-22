import unittest
from unittest.mock import patch

from app import app, create_enemy, load_questions


class RoguelikeGameTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()
        self.client.post("/api/start")

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

    def test_new_run_starts_with_seven_hp_and_visible_intent(self):
        response = self.client.get("/api/question")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["room"], 1)
        self.assertEqual(data["hp"], 7)
        self.assertEqual(data["enemy"]["hp"], 2)
        self.assertEqual(data["enemy"]["intent_detail"]["id"], "attack")

    def test_session_cookie_stays_within_browser_limit(self):
        response = self.client.post("/api/start")
        cookie = response.headers.get("Set-Cookie", "")
        self.assertLess(len(cookie), 4093)

    def test_wrong_answer_removes_hp_but_run_continues(self):
        correct_answer = self.answer_for_current_question()
        wrong_answer = next(key for key in "ABCD" if key != correct_answer)

        response = self.client.post("/api/answer", json={"answer": wrong_answer})
        data = response.get_json()

        self.assertEqual(data["status"], "player_hit")
        self.assertEqual(data["hp"], 6)
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

        self.assertEqual(data["damage_dealt"], 2)
        self.assertEqual(data["enemy"]["hp"], 5)

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
        self.assertEqual(result["hp"], 7)

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
        self.assertEqual(result["damage_dealt"], 1)
        self.assertEqual(result["damage_taken"], 1)
        self.assertEqual(result["hp"], 6)
        self.assertEqual(result["enemy"]["hp"], 1)

    def test_correct_defend_interrupts_enemy_intent(self):
        result = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "defend"},
        ).get_json()

        self.assertEqual(result["damage_dealt"], 0)
        self.assertEqual(result["damage_taken"], 0)
        self.assertTrue(result["enemy_action"]["canceled"])
        self.assertEqual(result["hp"], 7)

    def test_correct_exploit_deals_double_damage_and_interrupts(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"]["hp"] = 3
            state["enemy"]["max_hp"] = 3
            flask_session["game_state"] = state

        result = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "exploit"},
        ).get_json()

        self.assertEqual(result["damage_dealt"], 2)
        self.assertEqual(result["damage_taken"], 0)
        self.assertTrue(result["enemy_action"]["canceled"])
        self.assertEqual(result["enemy"]["hp"], 1)

    def test_wrong_exploit_increases_incoming_attack(self):
        correct = self.answer_for_current_question()
        wrong = next(key for key in "ABCD" if key != correct)
        result = self.client.post(
            "/api/answer", json={"answer": wrong, "combat_action": "exploit"}
        ).get_json()

        self.assertEqual(result["damage_taken"], 2)
        self.assertEqual(result["hp"], 5)

    def test_zero_trust_blocks_only_first_damaging_attack_in_battle(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["relics"] = ["zero_trust"]
            state["enemy"]["hp"] = 4
            state["enemy"]["max_hp"] = 4
            flask_session["game_state"] = state

        first = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "attack"},
        ).get_json()
        self.assertEqual(first["blocked_by"], "Zero Trust")
        self.assertEqual(first["hp"], 7)

        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            state["enemy"]["intent"] = "attack"
            flask_session["game_state"] = state
        second = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question(), "combat_action": "attack"},
        ).get_json()
        self.assertIsNone(second["blocked_by"])
        self.assertEqual(second["hp"], 6)

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
        self.assertEqual(data["time_limit"], 20)

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


if __name__ == "__main__":
    unittest.main()

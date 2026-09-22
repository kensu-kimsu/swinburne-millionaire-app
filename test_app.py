import unittest

from app import app, create_enemy, load_questions


class RoguelikeGameTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()
        self.client.post("/api/start")

    def answer_for_current_question(self):
        with self.client.session_transaction() as flask_session:
            state = flask_session["game_state"]
            question_index = state["question_order"][state["question_number"]]
        return load_questions()[question_index]["answer"]

    def test_new_run_starts_with_five_hp(self):
        response = self.client.get("/api/question")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["room"], 1)
        self.assertEqual(data["hp"], 5)
        self.assertEqual(data["enemy"]["hp"], 1)

    def test_wrong_answer_removes_hp_but_run_continues(self):
        correct_answer = self.answer_for_current_question()
        wrong_answer = next(key for key in "ABCD" if key != correct_answer)

        response = self.client.post("/api/answer", json={"answer": wrong_answer})
        data = response.get_json()

        self.assertEqual(data["status"], "player_hit")
        self.assertEqual(data["hp"], 4)
        self.assertEqual(data["room"], 1)

    def test_correct_answer_clears_a_normal_room(self):
        response = self.client.post(
            "/api/answer",
            json={"answer": self.answer_for_current_question()},
        )
        data = response.get_json()

        self.assertEqual(data["status"], "room_cleared")
        self.assertEqual(data["room"], 2)
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
        self.assertEqual(data["enemy"]["hp"], 1)

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
        self.assertTrue(data["enemy"]["hp"] == 0)


if __name__ == "__main__":
    unittest.main()

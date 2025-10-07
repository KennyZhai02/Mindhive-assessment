import unittest
from chatbot.agent import ConversationAgent

class TestConversationAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ConversationAgent()

    def test_happy_path_three_turns(self):
        """Test: User → Bot → User → Bot flow"""
        # Turn 1
        resp1 = self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.assertIn("Which outlet", resp1)  # Follow-up expected
        self.assertEqual(self.agent.slots["current_city"], "Petaling Jaya")

        # Turn 2
        resp2 = self.agent.process_turn("SS 2, whats the opening time?")
        self.assertIn("9:00AM", resp2)  # Confirms outlet and time
        self.assertEqual(self.agent.slots["current_outlet"], "SS 2")

        # Turn 3
        resp3 = self.agent.process_turn("What about Bangsar?")
        self.assertIn("Which outlet", resp3)  # New outlet → ask again
        self.assertEqual(self.agent.slots["current_outlet"], "Bangsar")

    def test_interrupted_path(self):
        """Test: User abandons context mid-flow"""
        resp1 = self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.assertIn("Which outlet", resp1)

        # User changes topic
        resp2 = self.agent.process_turn("Tell me a joke")
        self.assertNotIn("Which outlet", resp2)  # Should not force follow-up
        self.assertIsNone(self.agent.slots["current_outlet"])  # Slot cleared?

        # But memory still retains history
        self.assertTrue(len(self.agent.memory.load_memory_variables({})["history"]) > 0)

    def test_slot_reset(self):
        """Test: Reset clears all slots and memory"""
        self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.assertIsNotNone(self.agent.slots["current_city"])
        self.agent.reset()
        self.assertIsNone(self.agent.slots["current_city"])
        self.assertIsNone(self.agent.slots["current_outlet"])
        self.assertEqual(len(self.agent.memory.load_memory_variables({})["history"]), 0)

    def test_no_intent_fallback(self):
        """Test: Unknown intent falls back to LLM"""
        resp = self.agent.process_turn("Hello, how are you?")
        self.assertIsInstance(resp, str)
        self.assertGreater(len(resp), 0)

if __name__ == "__main__":
    unittest.main()
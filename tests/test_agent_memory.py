import unittest
import re
from unittest.mock import Mock
from chatbot.agent import ConversationAgent

class MockLLM:
    def invoke(self, prompt: str):
        return Mock(content="I'm a friendly coffee bot!")

class TestConversationAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ConversationAgent(llm=MockLLM())

    def test_happy_path_three_turns(self):
        resp1 = self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.assertIn("Which outlet", resp1)
        self.assertEqual(self.agent.slots["current_city"], "Petaling Jaya")

        resp2 = self.agent.process_turn("SS 2, whats the opening time?")
        self.assertTrue(re.search(r'\d{1,2}:\d{2}AM', resp2))
        self.assertEqual(self.agent.slots["current_outlet"], "SS 2")

        resp3 = self.agent.process_turn("What about Bangsar?")
        self.assertTrue(re.search(r'\d{1,2}:\d{2}AM', resp3))
        self.assertEqual(self.agent.slots["current_outlet"], "Bangsar")

    def test_interrupted_path(self):
        resp1 = self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.assertIn("Which outlet", resp1)
        resp2 = self.agent.process_turn("Tell me a joke")
        self.assertEqual(resp2, "I'm a friendly coffee bot!")

    def test_slot_reset(self):
        self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.agent.reset()
        self.assertIsNone(self.agent.slots["current_city"])
        self.assertIsNone(self.agent.slots["current_outlet"])

    def test_no_intent_fallback(self):
        resp = self.agent.process_turn("Hello!")
        self.assertEqual(resp, "I'm a friendly coffee bot!")
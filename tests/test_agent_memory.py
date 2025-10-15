import unittest
import re
from unittest.mock import Mock, patch
from chatbot.agent import ConversationAgent

class MockLLM:
    def invoke(self, prompt: str):
        return Mock(content="I'm a friendly coffee bot!")

class TestConversationAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ConversationAgent(llm=MockLLM())

    @patch('chatbot.tools.OutletSQLTool.run')
    def test_happy_path_three_turns(self, mock_outlet):
        mock_outlet.side_effect = [
            {  
                "results": [{
                    "name": "SS 2",
                    "address": "Jalan SS 2/67",
                    "opening_hours": "8:00AM - 10:00PM"
                }]
            },
            { 
                "results": [{
                    "name": "Bangsar",
                    "address": "Jalan Maarof",
                    "opening_hours": "7:30AM - 9:30PM"
                }]
            }
        ]

        resp1 = self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.assertIn("Which outlet", resp1)
        self.assertEqual(self.agent.slots["current_city"], "Petaling Jaya")

        resp2 = self.agent.process_turn("SS 2, whats the opening time?")
        self.assertTrue(re.search(r'\d{1,2}:\d{2}AM', resp2))  
        self.assertEqual(self.agent.slots["current_outlet"], "SS 2")

        resp3 = self.agent.process_turn("What about Bangsar?")
        self.assertTrue(re.search(r'\d{1,2}:\d{2}AM', resp3))  
        self.assertEqual(self.agent.slots["current_outlet"], "Bangsar")
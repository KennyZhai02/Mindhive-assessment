import unittest
from unittest.mock import patch, Mock
from chatbot.agent import ConversationAgent

class MockLLM:
    def invoke(self, prompt: str):
        return Mock(content="Fallback response")

class TestPlanner(unittest.TestCase):
    def setUp(self):
        self.agent = ConversationAgent(llm=MockLLM())

    @patch('chatbot.tools.CalculatorTool.run')
    def test_calculate_intent(self, mock_calc):
        mock_calc.return_value = {"result": 30}
        resp = self.agent.process_turn("Calculate 5 * 6")
        self.assertIn("The result is 30", resp)

    def test_calculate_missing_expr(self):
        resp = self.agent.process_turn("Calculate")
        self.assertIn("What would you like to calculate", resp)

    @patch('chatbot.tools.ProductRAGTool.run')
    def test_product_intent(self, mock_prod):
        mock_prod.return_value = {"answer": "Tumblers are great!"}
        resp = self.agent.process_turn("Tell me about ZUS tumblers")
        self.assertIn("Tumblers are great!", resp)

    def test_outlet_intent_without_slot(self):
        resp = self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.assertIn("Which outlet are you referring to", resp)

    @patch('chatbot.tools.OutletSQLTool.run')
    def test_outlet_intent_with_slot(self, mock_outlet):
        mock_outlet.return_value = {
            "results": [  # ← MUST be a list under "results"
                {
                    "name": "SS 2",              # ← Use "name", not "outlet"
                    "address": "Jalan SS 2/67, Petaling Jaya",
                    "opening_hours": "8:00AM - 10:00PM"
                }
            ]
        }
        self.agent.slots["current_outlet"] = "SS 2"
        resp = self.agent.process_turn("What are the opening hours?")
        self.assertIn("8:00AM", resp)
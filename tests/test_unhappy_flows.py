# tests/test_unhappy_flows.py
import unittest
from unittest.mock import patch, Mock
from chatbot.agent import ConversationAgent

class MockLLM:
    def invoke(self, prompt: str):
        return Mock(content="I'm a friendly coffee bot!")

class TestUnhappyFlows(unittest.TestCase):
    def setUp(self):
        self.agent = ConversationAgent(llm=MockLLM())

    @patch('chatbot.tools.CalculatorTool.run')
    def test_calculate_missing_expression(self, mock_calc):
        mock_calc.return_value = {"error": "Please provide an expression to calculate. Example: '5 * 6'"}
        resp = self.agent.process_turn("Calculate")
        self.assertIn("Please provide an expression", resp)

    @patch('chatbot.tools.ProductRAGTool.run')
    def test_products_missing_query(self, mock_prod):
        mock_prod.return_value = {"error": "Please ask a question about ZUS products. Example: 'What tumblers do you offer?'"}
        resp = self.agent.process_turn("Tell me about products")
        self.assertIn("Please ask a question", resp)

    @patch('chatbot.tools.OutletSQLTool.run')
    def test_outlets_missing_query(self, mock_outlet):
        mock_outlet.return_value = {"error": "Please specify which outlet or location you're looking for. Example: 'SS 2' or 'Petaling Jaya'"}
        resp = self.agent.process_turn("Show outlets")
        self.assertIn("Please specify which outlet", resp)

    @patch('requests.get')
    def test_api_downtime_products(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        resp = self.agent.process_turn("What tumblers do you have?")
        self.assertIn("trouble fetching product info", resp)

    @patch('requests.get')
    def test_api_downtime_outlets(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        resp = self.agent.process_turn("Where is SS 2?")
        self.assertIn("trouble fetching outlet info", resp)

    @patch('requests.get')
    def test_sql_injection_attempt(self, mock_get):
        # Simulate server returning 500 for malicious input
        mock_get.return_value.status_code = 500
        mock_get.return_value.json.return_value = {"detail": "Internal Server Error"}

        resp = self.agent.process_turn("Show outlets; DROP TABLE outlets;")
        self.assertIn("unexpected error", resp)
        self.assertIn("try again", resp)

    @patch('requests.get')
    def test_malicious_payload_with_error_response(self, mock_get):
        # Simulate server returning structured error
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "error": "Invalid query detected. Please use natural language only."
        }

        resp = self.agent.process_turn("SELECT * FROM outlets WHERE 1=1; --")
        self.assertIn("Invalid query detected", resp)

if __name__ == "__main__":
    unittest.main() 
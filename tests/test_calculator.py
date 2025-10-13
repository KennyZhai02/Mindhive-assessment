import unittest
from unittest.mock import patch
from chatbot.tools import CalculatorTool

class TestCalculatorTool(unittest.TestCase):
    def setUp(self):
        self.tool = CalculatorTool()

    @patch('requests.post')
    def test_successful_calculation(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"result": 30}
        result = self.tool.run("5 * 6")
        self.assertEqual(result["result"], 30)

    @patch('requests.post')
    def test_division_by_zero(self, mock_post):
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"detail": "Cannot divide by zero"}
        result = self.tool.run("5 / 0")
        self.assertIn("Cannot divide by zero", result["error"])

    @patch('requests.post')
    def test_invalid_expression(self, mock_post):
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"detail": "Invalid characters"}
        result = self.tool.run("5 + x")
        self.assertIn("Invalid characters", result["error"])
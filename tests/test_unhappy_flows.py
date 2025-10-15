import unittest
from unittest.mock import patch, Mock
from chatbot.agent import ConversationAgent
from chatbot.tools import CalculatorTool, ProductRAGTool, OutletSQLTool
import requests

class MockLLM:
    def invoke(self, prompt: str):
        return Mock(content="I'm a friendly coffee bot!")

class TestUnhappyFlows(unittest.TestCase):
    """Test suite for error handling and edge cases"""
    
    def setUp(self):
        self.agent = ConversationAgent(llm=MockLLM())
    
    def test_calculate_without_expression(self):
        """Test calculator with missing expression"""
        resp = self.agent.process_turn("Calculate")
        self.assertIn("What would you like to calculate", resp.lower())
        self.assertIn("example", resp.lower())
    
    def test_calculate_with_empty_string(self):
        """Test calculator with empty expression"""
        tool = CalculatorTool()
        result = tool.run("   ")
        self.assertIn("error", result)
        self.assertIn("provide an expression", result["error"].lower())
    
    def test_outlets_without_location(self):
        """Test outlet search without specifying location"""
        resp = self.agent.process_turn("Show me outlets")
        self.assertIn("which outlet", resp.lower())
    
    def test_products_vague_query(self):
        """Test product search with vague query"""
        resp = self.agent.process_turn("Tell me about products")
        self.assertTrue(len(resp) > 0)
    
    @patch('requests.post')
    def test_calculator_api_down(self, mock_post):
        """Test calculator when API is unreachable"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        tool = CalculatorTool()
        result = tool.run("5 + 5")
        
        self.assertIn("error", result)
        self.assertIn("trouble reaching", result["error"].lower())
        self.assertIn("try again", result["error"].lower())
    
    @patch('requests.post')
    def test_calculator_api_timeout(self, mock_post):
        """Test calculator when API times out"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        tool = CalculatorTool()
        result = tool.run("10 * 20")
        
        self.assertIn("error", result)
        self.assertIn("trouble", result["error"].lower())
    
    @patch('requests.post')
    def test_calculator_api_500_error(self, mock_post):
        """Test calculator when API returns 500"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_post.return_value = mock_response
        
        tool = CalculatorTool()
        result = tool.run("7 + 3")
        
        self.assertIn("error", result)
    
    @patch('requests.get')
    def test_products_api_down(self, mock_get):
        """Test products RAG when API is down"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        tool = ProductRAGTool()
        result = tool.run("What tumblers do you have?")
        
        self.assertIn("error", result)
        self.assertIn("trouble fetching product", result["error"].lower())
    
    @patch('requests.get')
    def test_outlets_api_down(self, mock_get):
        """Test outlets when API is down"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        tool = OutletSQLTool()
        result = tool.run("SS 2 outlet")
        
        self.assertIn("error", result)
        self.assertIn("trouble fetching outlet", result["error"].lower())

    
    def test_sql_injection_classic(self):
        """Test classic SQL injection attempt"""
        malicious_queries = [
            "1'; DROP TABLE outlets--",
            "' OR '1'='1",
            "'; DELETE FROM outlets WHERE '1'='1",
            "1' UNION SELECT * FROM outlets--"
        ]
        
        for query in malicious_queries:
            with self.subTest(query=query):
                tool = OutletSQLTool()
                with patch('requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 400
                    mock_response.json.return_value = {"detail": "Malicious SQL detected"}
                    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
                    mock_get.return_value = mock_response
                    
                    result = tool.run(query)
                    self.assertTrue("error" in result or len(result) == 0)
    
    def test_calculator_code_injection(self):
        """Test code injection attempts in calculator"""
        malicious_expressions = [
            "__import__('os').system('ls')",
            "exec('print(1)')",
            "eval('1+1')",
            "1; import os",
        ]
        
        tool = CalculatorTool()
        
        for expr in malicious_expressions:
            with self.subTest(expr=expr):
                with patch('requests.post') as mock_post:
                    mock_response = Mock()
                    mock_response.status_code = 400
                    mock_response.json.return_value = {"detail": "Invalid characters in expression"}
                    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
                    mock_post.return_value = mock_response
                    
                    result = tool.run(expr)
                    self.assertIn("error", result)
    
    def test_xss_attempt_in_query(self):
        """Test XSS attempt in search queries"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "'; alert('XSS'); //",
            "<img src=x onerror=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            with self.subTest(payload=payload):
                resp = self.agent.process_turn(payload)
                self.assertTrue(len(resp) > 0)
                self.assertNotIn("<script>", resp)
    
    def test_extremely_long_input(self):
        """Test handling of extremely long input"""
        long_input = "A" * 10000
        resp = self.agent.process_turn(long_input)
        self.assertTrue(len(resp) > 0)
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        special_inputs = [
            "café ☕",
            "你好",
            "Проверка",
            "🎉🎊🎈"
        ]
        
        for inp in special_inputs:
            with self.subTest(input=inp):
                resp = self.agent.process_turn(inp)
                self.assertTrue(len(resp) > 0)
    
    def test_division_by_zero(self):
        """Test division by zero handling"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Cannot divide by zero"}
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
            mock_post.return_value = mock_response
            
            tool = CalculatorTool()
            result = tool.run("10 / 0")
            
            self.assertIn("error", result)
    
    def test_malformed_json_response(self):
        """Test handling of malformed API responses"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            
            tool = OutletSQLTool()
            result = tool.run("SS 2")
            
            self.assertIn("error", result)
    
    def test_empty_api_response(self):
        """Test handling when API returns empty results"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_get.return_value = mock_response
            
            tool = OutletSQLTool()
            result = tool.run("Nonexistent Outlet XYZ")
            
            self.assertIn("error", result)
            self.assertIn("no outlets found", result["error"].lower())
    
    def test_concurrent_slot_updates(self):
        """Test handling of rapid slot updates"""
        self.agent.process_turn("Is there an outlet in Petaling Jaya?")
        self.agent.process_turn("Actually, I meant Kuala Lumpur")
        resp = self.agent.process_turn("Show me Bangsar outlet")
        self.assertEqual(self.agent.slots["current_outlet"], "Bangsar")
        self.assertTrue(len(resp) > 0)
    
    def test_context_switch(self):
        """Test switching between different intents"""
        self.agent.process_turn("Calculate 5 + 5")
        resp = self.agent.process_turn("What products do you have?")
        self.assertTrue(len(resp) > 0)
        self.assertEqual(self.agent.slots["last_intent"], "product")


class TestSecurityMeasures(unittest.TestCase):
    """Additional security-focused tests"""
    
    def test_path_traversal_attempt(self):
        """Test path traversal attempts"""
        agent = ConversationAgent(llm=MockLLM())
        dangerous_inputs = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f",
        ]
        
        for inp in dangerous_inputs:
            with self.subTest(input=inp):
                resp = agent.process_turn(inp)
                self.assertNotIn("/etc/", resp)
                self.assertNotIn("C:\\", resp)
    
    def test_command_injection_attempt(self):
        """Test command injection attempts"""
        agent = ConversationAgent(llm=MockLLM())
        dangerous_inputs = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(rm -rf /)"
        ]
        
        for inp in dangerous_inputs:
            with self.subTest(input=inp):
                resp = agent.process_turn(inp)
                self.assertTrue(len(resp) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
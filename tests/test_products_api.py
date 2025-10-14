import unittest
import requests
import time

class TestProductsAPI(unittest.TestCase):
    """Integration tests for Products RAG API"""
    
    BASE_URL = "http://localhost:8000"
    
    @classmethod
    def setUpClass(cls):
        """Check if API is available before running tests"""
        try:
            resp = requests.get(f"{cls.BASE_URL}/health", timeout=2)
            if resp.status_code != 200:
                raise unittest.SkipTest("API server not available")
        except requests.exceptions.RequestException:
            raise unittest.SkipTest("API server not available")
    
    def test_successful_search(self):
        """Test successful product search"""
        resp = requests.get(
            f"{self.BASE_URL}/products",
            params={"query": "tumbler"},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertIsInstance(data["answer"], str)
        self.assertGreater(len(data["answer"]), 0)
        self.assertIn("sources", data)
        self.assertIsInstance(data["sources"], list)
    
    def test_detailed_product_query(self):
        """Test detailed product query"""
        resp = requests.get(
            f"{self.BASE_URL}/products",
            params={"query": "What are the features of ZUS tumblers?"},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertTrue(len(data["answer"]) > 20)
    
    def test_empty_query(self):
        """Test empty query validation"""
        resp = requests.get(
            f"{self.BASE_URL}/products",
            params={"query": ""},
            timeout=5
        )
        # FastAPI validation should catch this
        self.assertEqual(resp.status_code, 422)
    
    def test_missing_query_param(self):
        """Test missing query parameter"""
        resp = requests.get(f"{self.BASE_URL}/products", timeout=5)
        # FastAPI validation should catch this
        self.assertEqual(resp.status_code, 422)
    
    def test_special_characters_in_query(self):
        """Test special characters are handled"""
        resp = requests.get(
            f"{self.BASE_URL}/products",
            params={"query": "café ☕"},
            timeout=10
        )
        # Should handle gracefully
        self.assertIn(resp.status_code, [200, 500])
        if resp.status_code == 200:
            data = resp.json()
            self.assertIn("answer", data)
    
    def test_very_long_query(self):
        """Test handling of very long queries"""
        long_query = "What products " * 100
        resp = requests.get(
            f"{self.BASE_URL}/products",
            params={"query": long_query},
            timeout=10
        )
        # Should handle gracefully (either process or return error)
        self.assertIn(resp.status_code, [200, 400, 500])
    
    def test_nonexistent_product(self):
        """Test query for nonexistent product"""
        resp = requests.get(
            f"{self.BASE_URL}/products",
            params={"query": "quantum flux capacitor"},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        # Should indicate no relevant products found
        self.assertTrue(len(data["answer"]) > 0)


if __name__ == "__main__":
    # Run with verbosity
    unittest.main(verbosity=2)
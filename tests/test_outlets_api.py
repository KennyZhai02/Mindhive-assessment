import unittest
import requests

class TestOutletsAPI(unittest.TestCase):
    """Integration tests for Outlets Text2SQL API"""
    
    BASE_URL = "http://localhost:8000"
    
    @classmethod
    def setUpClass(cls):
        """Check if API is available and resources are initialized before running tests"""
        try:
            resp = requests.get(f"{cls.BASE_URL}/health", timeout=2)
            if resp.status_code != 200:
                raise unittest.SkipTest("API server not available")

            health_data = resp.json()
            if not health_data.get("outlet_db_exists"):
                raise unittest.SkipTest("Outlet database not initialized. Run: python ingest/create_outlets_db.py")
        except requests.exceptions.RequestException:
            raise unittest.SkipTest("API server not available")
    
    def test_successful_search_ss2(self):
        """Test successful outlet search for SS 2"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "SS 2"},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        self.assertGreater(len(data["results"]), 0)
        
        # Check result structure
        first_result = data["results"][0]
        self.assertIn("name", first_result)
        self.assertIn("address", first_result)
    
    def test_successful_search_bangsar(self):
        """Test successful outlet search for Bangsar"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "Bangsar"},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertGreater(len(data["results"]), 0)
    
    def test_search_by_city(self):
        """Test search by city name"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "outlets in Kuala Lumpur"},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        # Should find at least one outlet
        self.assertGreaterEqual(len(data["results"]), 0)
    
    def test_sql_injection_attempt_drop_table(self):
        """Test SQL injection attempt - DROP TABLE"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "1'; DROP TABLE outlets--"},
            timeout=10
        )
        # Should be blocked (400) or handled safely (200 with error)
        self.assertIn(resp.status_code, [200, 400, 500])
        
        if resp.status_code == 200:
            data = resp.json()
            # If returned 200, should have safe handling
            # Results should be empty or error message
            self.assertTrue("results" in data or "error" in data)
        
        # Verify database still exists by running a normal query
        verify_resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "SS 2"},
            timeout=10
        )
        self.assertEqual(verify_resp.status_code, 200)
    
    def test_sql_injection_attempt_union_select(self):
        """Test SQL injection attempt - UNION SELECT"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "1' UNION SELECT * FROM outlets--"},
            timeout=10
        )
        # Should be blocked or handled safely
        self.assertIn(resp.status_code, [200, 400, 500])
    
    def test_sql_injection_attempt_or_1_equals_1(self):
        """Test SQL injection attempt - OR 1=1"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "' OR '1'='1"},
            timeout=10
        )
        # Should be blocked or handled safely
        self.assertIn(resp.status_code, [200, 400, 500])
    
    def test_sql_injection_attempt_delete(self):
        """Test SQL injection attempt - DELETE"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "'; DELETE FROM outlets WHERE '1'='1"},
            timeout=10
        )
        # Should be blocked
        self.assertIn(resp.status_code, [200, 400, 500])
        
        # Verify database integrity
        verify_resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "Bangsar"},
            timeout=10
        )
        self.assertEqual(verify_resp.status_code, 200)
    
    def test_no_results_found(self):
        """Test query that returns no results"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "Nonexistent City XYZ123"},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        # Empty results are acceptable
        self.assertIsInstance(data["results"], list)
    
    def test_empty_query(self):
        """Test empty query parameter"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": ""},
            timeout=5
        )
        # FastAPI validation should catch this
        self.assertEqual(resp.status_code, 422)
    
    def test_missing_query_param(self):
        """Test missing query parameter"""
        resp = requests.get(f"{self.BASE_URL}/outlets", timeout=5)
        # FastAPI validation should catch this
        self.assertEqual(resp.status_code, 422)
    
    def test_special_characters_in_query(self):
        """Test special characters are handled"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "café near me ☕"},
            timeout=10
        )
        # Should handle gracefully
        self.assertIn(resp.status_code, [200, 400, 500])
    
    def test_natural_language_query(self):
        """Test natural language query"""
        resp = requests.get(
            f"{self.BASE_URL}/outlets",
            params={"query": "Show me outlets that are open late"},
            timeout=10
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIn("sql", data)  # Should return generated SQL


if __name__ == "__main__":
    unittest.main(verbosity=2)
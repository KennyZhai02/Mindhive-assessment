# tests/test_outlets_api.py
import unittest
import requests

class TestOutletsAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"

    def test_successful_search(self):
        resp = requests.get(f"{self.BASE_URL}/outlets", params={"query": "SS 2"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertGreater(len(data["results"]), 0)

    def test_sql_injection_attempt(self):
        # Malicious payload
        resp = requests.get(f"{self.BASE_URL}/outlets", params={"query": "1'; DROP TABLE outlets--"})
        self.assertEqual(resp.status_code, 500)  # Should fail gracefully
        data = resp.json()
        self.assertIn("error", data)

    def test_no_results(self):
        resp = requests.get(f"{self.BASE_URL}/outlets", params={"query": "Nonexistent Outlet"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["results"]), 0)
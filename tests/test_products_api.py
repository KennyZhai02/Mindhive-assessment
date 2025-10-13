# tests/test_products_api.py
import unittest
import requests

class TestProductsAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"

    def test_successful_search(self):
        resp = requests.get(f"{self.BASE_URL}/products", params={"query": "tumbler"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answer", data)
        self.assertIsInstance(data["sources"], list)

    def test_empty_query(self):
        resp = requests.get(f"{self.BASE_URL}/products", params={"query": ""})
        self.assertEqual(resp.status_code, 422)  # FastAPI validation

    def test_server_error(self):
        # Simulate server error by using invalid path
        resp = requests.get(f"{self.BASE_URL}/products_invalid")
        self.assertEqual(resp.status_code, 404)
import requests
from typing import Dict, Any

class CalculatorTool:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def run(self, expression: str) -> Dict[str, Any]:
        if not expression.strip():
            return {"error": "Please provide an expression. Example: '5 * 6'"}
        try:
            resp = requests.post(f"{self.base_url}/calculate", json={"expr": expression}, timeout=5)
            resp.raise_for_status()
            return {"result": resp.json()["result"]}
        except Exception as e:
            return {"error": "I'm having trouble reaching the calculator. Please try again later."}

class ProductRAGTool:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def run(self, query: str) -> Dict[str, Any]:
        if not query.strip():
            return {"error": "Please ask about a product. Example: 'What tumblers do you offer?'"}
        try:
            resp = requests.get(f"{self.base_url}/products", params={"query": query}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return {"answer": data["answer"], "sources": data["sources"]}
        except Exception as e:
            return {"error": "I'm having trouble fetching product info. Please try again later."}

class OutletSQLTool:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def run(self, nl_query: str) -> Dict[str, Any]:
        if not nl_query.strip():
            return {"error": "Please specify an outlet or location. Example: 'SS 2'"}
        try:
            resp = requests.get(f"{self.base_url}/outlets", params={"query": nl_query}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                return {"error": data["error"]}
            if not data.get("results"):
                return {"error": "No outlets found. Try a different name."}
            return {"results": data["results"]}
        except Exception as e:
            return {"error": "I'm having trouble fetching outlet info. Please try again later."}
import requests
from typing import Dict, Any
import os

MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

class CalculatorTool:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or BASE_URL

    def run(self, expression: str) -> Dict[str, Any]:
        """Run calculator - works in both real and mock mode"""
        if not expression.strip():
            return {"error": "Please provide a mathematical expression. Example: '5 * 6'"}
        
        try:
            # Calculator doesn't need OpenAI, so call the API directly
            resp = requests.post(
                f"{self.base_url}/calculate",
                json={"expr": expression},
                timeout=5
            )
            resp.raise_for_status()
            return {"result": resp.json()["result"]}
        except requests.exceptions.Timeout:
            return {"error": "The calculator is taking too long to respond. Please try again."}
        except requests.exceptions.ConnectionError:
            return {"error": "I'm having trouble reaching the calculator service. Please try again later."}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_detail = e.response.json().get("detail", "Invalid expression")
                return {"error": f"Invalid expression: {error_detail}"}
            return {"error": "I'm having trouble with that calculation. Please try a different expression."}
        except Exception as e:
            return {"error": f"Calculation error. Please check your expression and try again."}


class ProductRAGTool:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or BASE_URL
        
        # Mock responses for common queries
        self.mock_responses = {
            "tumbler": {
                "answer": "We offer several great tumbler options! The **OG CUP 2.0** (RM 49.90) features a screw-on lid and double-wall insulation. The **All-Can Tumbler** (RM 59.90) is versatile and fits standard cans. The **All Day Cup** (RM 49.90) is perfect for daily use with various designs.",
                "sources": [
                    {"title": "OG CUP 2.0", "price": "RM 49.90"},
                    {"title": "All-Can Tumbler", "price": "RM 59.90"},
                    {"title": "All Day Cup", "price": "RM 49.90"}
                ]
            },
            "mug": {
                "answer": "We have two excellent mug options: The **OG Ceramic Mug** (RM 39.90) is microwave and dishwasher safe, perfect for your morning coffee. The **ZUS Stainless Steel Mug** (RM 44.90) features double-wall insulation.",
                "sources": [
                    {"title": "OG Ceramic Mug", "price": "RM 39.90"},
                    {"title": "ZUS Stainless Steel Mug", "price": "RM 44.90"}
                ]
            },
            "price": {
                "answer": "Our drinkware prices range from RM 39.90 to RM 59.90. Ceramic mugs start at RM 39.90, standard tumblers at RM 49.90, and premium tumblers at RM 59.90.",
                "sources": [{"title": "Price Range", "price": "RM 39.90 - 59.90"}]
            }
        }

    def run(self, query: str) -> Dict[str, Any]:
        """Search products - uses API or mock responses"""
        if not query.strip():
            return {"error": "Please ask about a product. Example: 'What tumblers do you offer?'"}
        
        try:
            resp = requests.get(
                f"{self.base_url}/products",
                params={"query": query},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            return {"answer": data["answer"], "sources": data.get("sources", [])}
        
        except requests.exceptions.Timeout:
            return {"error": "The product search is taking too long. Please try again."}
        except requests.exceptions.ConnectionError:
            # Fallback to mock response if API is unreachable
            query_lower = query.lower()
            for key, response in self.mock_responses.items():
                if key in query_lower:
                    return response
            return {
                "answer": "We offer a variety of drinkware including tumblers, mugs, and accessories. What specific product are you interested in?",
                "sources": []
            }
        except Exception as e:
            return {"error": "I'm having trouble fetching product info. Please try again later."}


class OutletSQLTool:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or BASE_URL
        
        # Mock outlet data
        self.mock_outlets = {
            "ss 2": {
                "name": "ZUS Coffee - SS 2",
                "address": "No. 75, Jalan SS 2/67, SS 2, 47300 Petaling Jaya, Selangor",
                "opening_hours": "8:00 AM - 10:00 PM",
                "services": "Dine-in, Takeaway, Delivery, Drive-thru"
            },
            "bangsar": {
                "name": "ZUS Coffee - Bangsar",
                "address": "No. 11, Jalan Telawi 3, Bangsar Baru, 59100 Kuala Lumpur",
                "opening_hours": "7:00 AM - 11:00 PM",
                "services": "Dine-in, Takeaway, Delivery"
            },
            "klcc": {
                "name": "ZUS Coffee - KLCC",
                "address": "Lot 241, Level 2, Suria KLCC, 50088 Kuala Lumpur",
                "opening_hours": "9:00 AM - 10:00 PM",
                "services": "Dine-in, Takeaway"
            },
            "subang": {
                "name": "ZUS Coffee - Subang Jaya",
                "address": "G-01, Jalan SS 15/4d, SS 15, 47500 Subang Jaya, Selangor",
                "opening_hours": "7:30 AM - 10:00 PM",
                "services": "Dine-in, Takeaway, Delivery"
            },
            "damansara": {
                "name": "ZUS Coffee - Damansara Jaya",
                "address": "C01A, Atria Shopping Gallery, Jalan SS 22/23, 47400 Petaling Jaya",
                "opening_hours": "8:00 AM - 10:00 PM",
                "services": "Dine-in, Takeaway, Delivery"
            }
        }

    def run(self, nl_query: str) -> Dict[str, Any]:
        """Search outlets - uses API or mock data"""
        if not nl_query.strip():
            return {"error": "Please specify an outlet or location. Example: 'SS 2' or 'Bangsar'"}
        
        try:
            resp = requests.get(
                f"{self.base_url}/outlets",
                params={"query": nl_query},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            
            if "error" in data:
                return {"error": data["error"]}
            
            if not data.get("results"):
                return {"error": "No outlets found. Try a different location like 'SS 2' or 'Bangsar'."}
            
            return {"results": data["results"]}
        
        except requests.exceptions.Timeout:
            return {"error": "The outlet search is taking too long. Please try again."}
        except requests.exceptions.ConnectionError:
            # Fallback to mock data
            query_lower = nl_query.lower()
            for key, outlet in self.mock_outlets.items():
                if key in query_lower:
                    return {"results": [outlet]}
            
            # Return all if no specific match
            return {"results": list(self.mock_outlets.values())[:3]}
        except Exception as e:
            return {"error": "I'm having trouble fetching outlet info. Please try again later."}
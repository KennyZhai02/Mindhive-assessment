import requests
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CalculatorTool:
    """Calculator tool that safely evaluates mathematical expressions"""
    
    def run(self, expression: str) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression safely.
        
        Args:
            expression: Mathematical expression string
            
        Returns:
            Dict with 'result' on success or 'error' on failure
        """
        if not expression.strip():
            return {"error": "Please provide an expression. Example: '5 * 6'"}
        
        try:
            # Security: Only allow safe mathematical characters
            if not all(c in "0123456789+-*/(). " for c in expression):
                return {"error": "Invalid characters in expression. Only numbers and +, -, *, /, () are allowed."}
            
            # Safe eval with no builtins access
            result = eval(expression, {"__builtins__": {}}, {})
            return {"result": result}
            
        except ZeroDivisionError:
            return {"error": "Cannot divide by zero"}
        except SyntaxError:
            return {"error": "Invalid mathematical expression. Please check your syntax."}
        except Exception as e:
            logger.error(f"Calculator error: {e}")
            return {"error": f"Calculation error: {str(e)}"}


class ProductRAGTool:
    """Product search tool using RAG API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Search for products using RAG.
        
        Args:
            query: Search query string
            
        Returns:
            Dict with 'answer' and 'sources' on success or 'error' on failure
        """
        if not query.strip():
            return {"error": "Please ask about a product. Example: 'What tumblers do you offer?'"}
        
        try:
            resp = requests.get(
                f"{self.base_url}/products",
                params={"query": query},
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            
            return {
                "answer": data.get("answer", "No information found."),
                "sources": data.get("sources", [])
            }
            
        except requests.exceptions.Timeout:
            logger.error("Product API timeout")
            return {"error": "I'm having trouble reaching the product database. Please try again in a moment."}
        
        except requests.exceptions.ConnectionError:
            logger.error("Product API connection error")
            return {"error": "I'm having trouble connecting to the product service. Please try again later."}
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Product API HTTP error: {e}")
            if e.response.status_code == 500:
                return {"error": "The product service is currently unavailable. Please try again later."}
            return {"error": "I'm having trouble fetching product info. Please try again later."}
        
        except ValueError as e:
            logger.error(f"Product API JSON decode error: {e}")
            return {"error": "I received an invalid response from the product service. Please try again."}
        
        except Exception as e:
            logger.error(f"Product API unexpected error: {e}")
            return {"error": "I'm having trouble fetching product info. Please try again later."}


class OutletSQLTool:
    """Outlet search tool using Text2SQL API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def run(self, nl_query: str) -> Dict[str, Any]:
        """
        Search for outlets using natural language.
        
        Args:
            nl_query: Natural language query
            
        Returns:
            Dict with 'results' list on success or 'error' on failure
        """
        if not nl_query.strip():
            return {"error": "Please specify an outlet or location. Example: 'SS 2'"}
        
        try:
            resp = requests.get(
                f"{self.base_url}/outlets",
                params={"query": nl_query},
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Check for API-level errors
            if "error" in data:
                return {"error": data["error"]}
            
            # Check for empty results
            if not data.get("results"):
                return {"error": "No outlets found. Try a different name or location."}
            
            return {"results": data["results"]}
            
        except requests.exceptions.Timeout:
            logger.error("Outlet API timeout")
            return {"error": "I'm having trouble reaching the outlet database. Please try again in a moment."}
        
        except requests.exceptions.ConnectionError:
            logger.error("Outlet API connection error")
            return {"error": "I'm having trouble connecting to the outlet service. Please try again later."}
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Outlet API HTTP error: {e}")
            if e.response.status_code == 400:
                # Security: Likely blocked malicious query
                return {"error": "I couldn't process that query. Please try a different search."}
            elif e.response.status_code == 500:
                return {"error": "The outlet service is currently unavailable. Please try again later."}
            return {"error": "I'm having trouble fetching outlet info. Please try again later."}
        
        except ValueError as e:
            logger.error(f"Outlet API JSON decode error: {e}")
            return {"error": "I received an invalid response from the outlet service. Please try again."}
        
        except Exception as e:
            logger.error(f"Outlet API unexpected error: {e}")
            return {"error": "I'm having trouble fetching outlet info. Please try again later."}
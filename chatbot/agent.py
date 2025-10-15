from langchain.memory import ConversationBufferMemory
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from typing import Optional
import re
import os
from .tools import CalculatorTool, ProductRAGTool, OutletSQLTool

# Check if mock mode is enabled
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

class MockLLM:
    """Simple mock LLM for responses when OpenAI is not available"""
    
    def invoke(self, prompt: str):
        """Return a simple fallback response"""
        class MockResponse:
            content = "I'm here to help! I can assist you with outlet locations, product information, or calculations. What would you like to know?"
        return MockResponse()

class ConversationAgent:
    def __init__(self, llm: Optional[BaseChatModel] = None):
        """Initialize conversation agent with optional mock mode"""
        
        if MOCK_MODE or not os.getenv("OPENAI_API_KEY"):
            # Use mock LLM when in mock mode or no API key
            self.llm = MockLLM()
            self.mock_mode = True
            print("🎭 Agent initialized in MOCK MODE")
        else:
            # Use real OpenAI LLM
            self.llm = llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
            self.mock_mode = False
            print("🤖 Agent initialized with OpenAI")
        
        self.memory = ConversationBufferMemory(return_messages=True)
        self.slots = {
            "current_city": None,
            "current_outlet": None,
            "last_intent": None,
            "last_user_input": "",
        }
        self.tools = {
            "calculator": CalculatorTool(),
            "products": ProductRAGTool(),
            "outlets": OutletSQLTool()
        }

    def update_slots(self, user_input: str) -> None:
        """Extract and update slot values from user input"""
        city_match = re.search(r'(Petaling Jaya|Kuala Lumpur|SS 2|Bangsar|Subang)', user_input, re.IGNORECASE)
        if city_match:
            self.slots["current_city"] = city_match.group(1)
        
        outlet_match = re.search(r'(SS 2|Bangsar|Subang|Damansara|KLCC|Mont Kiara|Sentul|Puchong)', user_input, re.IGNORECASE)
        if outlet_match:
            self.slots["current_outlet"] = outlet_match.group(1)

    def get_followup_prompt(self, intent: str) -> str:
        """Generate follow-up questions based on intent"""
        if intent == "outlet" and not self.slots["current_outlet"]:
            return "Yes! Which outlet are you referring to? (e.g., SS 2, Bangsar, KLCC)"
        elif intent == "calculate":
            return "What would you like to calculate? (e.g., 5 * 6)"
        return ""

    def parse_intent(self, user_input: str) -> str:
        """Classify user intent from input"""
        user_lower = user_input.lower()
        
        # Calculator intent
        if any(w in user_lower for w in ["calculate", "add", "subtract", "multiply", "divide", "+", "-", "*", "/"]):
            # Check if there's an actual math expression
            if re.search(r'\d+\s*[\+\-\*/]\s*\d+', user_input):
                return "calculate"
            if any(w in user_lower for w in ["calculate", "add", "subtract", "multiply", "divide"]):
                return "calculate"
        
        # Product intent
        if any(w in user_lower for w in ["product", "drinkware", "tumbler", "mug", "cup", "bottle", "price", "buy", "sell"]):
            return "product"
        
        # Outlet intent
        if any(w in user_lower for w in ["outlet", "store", "location", "branch", "open", "hours", "where", "address"]):
            return "outlet"
        
        # Check for specific outlet names
        if any(name in user_lower for name in ["ss 2", "ss2", "bangsar", "klcc", "subang", "damansara", "mont kiara"]):
            return "outlet"
        
        # Check for city names
        if any(city in user_lower for city in ["petaling jaya", "kuala lumpur", "kl", "selangor"]):
            return "outlet"
        
        return "unknown"

    def extract_calculation(self, user_input: str) -> str:
        """Extract mathematical expression from user input"""
        # Try to find a clear math expression
        match = re.search(r'([\d\+\-\*/\(\)\.\s]+)', user_input)
        if match:
            expr = match.group(1).strip()
            # Verify it contains an operator
            if any(op in expr for op in "+-*/"):
                return expr
        return ""

    def plan_action(self, intent: str, user_input: str) -> str:
        """Decide what action to take based on intent and context"""
        if intent == "calculate":
            expr = self.extract_calculation(user_input)
            if expr:
                self.slots["calc_expr"] = expr
                return "execute_calculator"
            else:
                return "ask_calc_expr"
        
        elif intent == "product":
            return "execute_products"
        
        elif intent == "outlet":
            if self.slots["current_outlet"]:
                return "execute_outlets"
            else:
                return "ask_outlet"
        
        else:
            return "fallback_llm"

    def execute_action(self, action: str) -> str:
        """Execute the planned action"""
        try:
            if action == "execute_calculator":
                result = self.tools["calculator"].run(self.slots.get("calc_expr", ""))
                if "error" in result:
                    return result["error"]
                return f"The result is {result['result']}"
            
            elif action == "execute_products":
                result = self.tools["products"].run(self.slots.get("last_user_input", ""))
                if "error" in result:
                    return result["error"]
                return result.get("answer", "No information found.")
            
            elif action == "execute_outlets":
                outlet_query = self.slots.get("current_outlet", "") + " outlet"
                result = self.tools["outlets"].run(outlet_query)
                
                if "error" in result:
                    return result["error"]
                
                if not result.get("results"):
                    return f"I couldn't find information about the {self.slots.get('current_outlet')} outlet. Please try another location."
                
                outlet = result["results"][0]
                return f"{outlet['name']} is located at {outlet['address']}. Operating hours: {outlet['opening_hours']}. Services: {outlet.get('services', 'Dine-in, Takeaway')}."
            
            return "I'm not sure how to help with that."
        
        except Exception as e:
            return f"I encountered an error: {str(e)}. Please try rephrasing your question."

    def process_turn(self, user_input: str) -> str:
        """Process a single conversation turn"""
        try:
            # Store the input
            self.slots["last_user_input"] = user_input
            
            # Update slots from input
            self.update_slots(user_input)
            
            # Parse intent
            intent = self.parse_intent(user_input)
            self.slots["last_intent"] = intent
            
            # Plan action
            action = self.plan_action(intent, user_input)
            
            # Execute action
            if action == "ask_calc_expr":
                return self.get_followup_prompt("calculate")
            
            elif action == "ask_outlet":
                return self.get_followup_prompt("outlet")
            
            elif action.startswith("execute_"):
                return self.execute_action(action)
            
            else:
                # Fallback to LLM (or mock response)
                if self.mock_mode:
                    # Provide helpful mock responses
                    user_lower = user_input.lower()
                    
                    if any(greeting in user_lower for greeting in ["hello", "hi", "hey"]):
                        return "Hello! I'm your ZUS Coffee assistant. I can help you find outlets, learn about our products, or do calculations. What would you like to know?"
                    
                    if "thank" in user_lower:
                        return "You're welcome! Is there anything else I can help you with?"
                    
                    if any(word in user_lower for word in ["help", "what can you do", "how"]):
                        return "I can help you with:\n• Finding ZUS Coffee outlet locations and hours\n• Information about our drinkware products (tumblers, mugs, accessories)\n• Simple calculations\n\nWhat would you like to know?"
                    
                    return "I'm here to help with ZUS Coffee outlets, products, or calculations. What would you like to know?"
                else:
                    # Use real LLM
                    history = self.memory.load_memory_variables({}).get("history", [])
                    history_text = "\n".join([str(msg) for msg in history])
                    prompt = f"{history_text}\nUser: {user_input}\nBot:"
                    response = self.llm.invoke(prompt)
                    self.memory.save_context({"input": user_input}, {"output": response.content})
                    return response.content
        
        except Exception as e:
            # Graceful error handling
            return f"I apologize, but I encountered an error. Please try asking in a different way. (Error: {str(e)})"

    def reset(self):
        """Reset conversation state"""
        self.memory.clear()
        self.slots = {
            "current_city": None,
            "current_outlet": None,
            "last_intent": None,
            "last_user_input": "",
            "calc_expr": None
        }
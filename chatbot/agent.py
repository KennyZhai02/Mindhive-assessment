from langchain.memory import ConversationBufferMemory
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from typing import Optional
import re
from .tools import CalculatorTool, ProductRAGTool, OutletSQLTool

class ConversationAgent:
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
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
        city_match = re.search(r'(Petaling Jaya|Kuala Lumpur|SS 2|Bangsar|Subang)', user_input, re.IGNORECASE)
        if city_match:
            self.slots["current_city"] = city_match.group(1)

        outlet_match = re.search(r'(SS 2|Bangsar|Subang|Damansara)', user_input, re.IGNORECASE)
        if outlet_match:
            self.slots["current_outlet"] = outlet_match.group(1)

    def get_followup_prompt(self, intent: str) -> str:
        if intent == "outlet" and not self.slots["current_outlet"]:
            return "Yes! Which outlet are you referring to? (e.g., SS 2, Bangsar)"
        elif intent == "calculate":
            return "what would you like to calculate? (e.g., 5 * 6)"
        return ""

    def parse_intent(self, user_input: str) -> str:
        user_lower = user_input.lower()
        # Check for calculation intent - but be more specific to avoid false positives
        calc_keywords = ["calculate", "add", "subtract", "multiply", "divide"]
        has_calc_keyword = any(w in user_lower for w in calc_keywords)
        has_math_expr = bool(re.search(r'\d+\s*[+\-*/]\s*\d+', user_input))

        if has_calc_keyword or has_math_expr:
            return "calculate"
        elif any(w in user_lower for w in ["product", "drinkware", "tumbler", "mug"]):
            return "product"
        elif any(w in user_lower for w in ["outlet", "store", "location", "open", "hours", "ss 2", "bangsar"]):
            return "outlet"
        else:
            return "unknown"

    def extract_calculation(self, user_input: str) -> str:
        match = re.search(r'([\d+\-*/().\s]+)', user_input)
        if match:
            expr = match.group(1).strip()
            if any(op in expr for op in "+-*/"):
                return expr
        return ""

    def plan_action(self, intent: str, user_input: str) -> str:
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
        if action == "execute_calculator":
            result = self.tools["calculator"].run(self.slots.get("calc_expr", ""))
            return result.get("error", f"The result is {result['result']}")
        elif action == "execute_products":
            result = self.tools["products"].run(self.slots.get("last_user_input", ""))
            return result.get("error", result.get("answer", "No info found."))
        elif action == "execute_outlets":
            result = self.tools["outlets"].run(self.slots.get("current_outlet", "") + " outlet")
            if "error" in result or not result.get("results"):
                return "I couldn't find that outlet."
            outlet = result["results"][0]
            return f"{outlet['name']} is at {outlet['address']}. Open {outlet['opening_hours']}."
        return "I'm not sure what to do."

    def process_turn(self, user_input: str) -> str:
        self.slots["last_user_input"] = user_input
        self.update_slots(user_input)
        intent = self.parse_intent(user_input)
        self.slots["last_intent"] = intent
        action = self.plan_action(intent, user_input)

        if action == "ask_calc_expr":
            return self.get_followup_prompt("calculate")
        elif action == "ask_outlet":
            return self.get_followup_prompt("outlet")
        elif action.startswith("execute_"):
            return self.execute_action(action)
        else:
            history = self.memory.load_memory_variables({}).get("history", [])
            history_text = "\n".join([str(msg) for msg in history])
            prompt = f"{history_text}\nUser: {user_input}\nBot:"
            response = self.llm.invoke(prompt)
            self.memory.save_context({"input": user_input}, {"output": response.content})
            return response.content

    def reset(self):
        self.memory.clear()
        self.slots = {
            "current_city": None,
            "current_outlet": None,
            "last_intent": None,
            "last_user_input": "",
            "calc_expr": None
        }
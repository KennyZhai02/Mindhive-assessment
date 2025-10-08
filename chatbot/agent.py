# chatbot/agent.py
from langchain.memory import ConversationBufferMemory
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from typing import Optional
import re


class ConversationAgent:
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
        self.memory = ConversationBufferMemory(return_messages=True)
        self.slots = {
            "current_city": None,
            "current_outlet": None,
            "last_intent": None
        }

    def update_slots(self, user_input: str) -> None:
        city_match = re.search(r'(Petaling Jaya|Kuala Lumpur|SS 2|Bangsar|Subang)', user_input, re.IGNORECASE)
        if city_match:
            self.slots["current_city"] = city_match.group(1)

        outlet_match = re.search(r'(SS 2|Bangsar|Subang|Damansara)', user_input, re.IGNORECASE)
        if outlet_match:
            self.slots["current_outlet"] = outlet_match.group(1)

    def get_followup_prompt(self, intent: str) -> str:
        if intent == "outlet_query" and not self.slots["current_outlet"]:
            return "Yes! Which outlet are you referring to?"
        elif intent == "opening_time" and not self.slots["current_outlet"]:
            return "I need to know which outlet you're asking about. Can you tell me the name?"
        return ""

    def process_turn(self, user_input: str) -> str:
        self.update_slots(user_input)

        intent = "unknown"
        user_lower = user_input.lower()

        if "outlet" in user_lower or "store" in user_lower:
            intent = "outlet_query"
        elif "opening time" in user_lower or "open" in user_lower or "hours" in user_lower:
            intent = "opening_time"
        elif any(name in user_lower for name in ["ss 2", "bangsar", "subang", "damansara", "petaling jaya"]):
            intent = "outlet_query"

        self.slots["last_intent"] = intent

        if intent == "outlet_query" and self.slots["current_city"]:
            if not self.slots["current_outlet"]:
                return self.get_followup_prompt(intent)
            else:
                return f"Ah yes, the {self.slots['current_outlet']} outlet opens at 9:00AM."
        elif intent == "opening_time" and self.slots["current_outlet"]:
            return f"Ah yes, the {self.slots['current_outlet']} outlet opens at 9:00AM."
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
            "last_intent": None
        }
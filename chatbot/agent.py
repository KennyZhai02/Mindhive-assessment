from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List
import re

class ConversationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
        self.memory = ConversationBufferMemory(return_messages=True)
        # Track slots across turns
        self.slots = {
            "current_city": None,
            "current_outlet": None,
            "last_intent": None
        }

    def update_slots(self, user_input: str) -> None:
        """Extract city/outlet from user input"""
        # Simple regex-based slot filling (can be enhanced with NER later)
        city_match = re.search(r'(Petaling Jaya|Kuala Lumpur|SS 2|Bangsar|Subang)', user_input, re.IGNORECASE)
        if city_match:
            self.slots["current_city"] = city_match.group(1)

        outlet_match = re.search(r'(SS 2|Bangsar|Subang|Damansara)', user_input, re.IGNORECASE)
        if outlet_match:
            self.slots["current_outlet"] = outlet_match.group(1)

    def get_followup_prompt(self, intent: str) -> str:
        """Generate follow-up question based on missing slots"""
        if intent == "outlet_query" and not self.slots["current_outlet"]:
            return f"Yes! Which outlet are you referring to? (e.g., SS 2, Bangsar, etc.)"
        elif intent == "opening_time" and not self.slots["current_outlet"]:
            return f"I need to know which outlet you're asking about. Can you tell me the name? (e.g., SS 2)"
        else:
            return ""

    def process_turn(self, user_input: str) -> str:
        """Main conversation loop with memory and slot tracking"""
        self.update_slots(user_input)

        # Classify intent (simplified for now)
        intent = "unknown"
        if "outlet" in user_input.lower() or "store" in user_input.lower():
            intent = "outlet_query"
        elif "opening time" in user_input.lower() or "open" in user_input.lower():
            intent = "opening_time"

        self.slots["last_intent"] = intent

        # Generate response
        if intent == "outlet_query" and self.slots["current_city"]:
            # If city is known but outlet not specified → ask follow-up
            if not self.slots["current_outlet"]:
                return self.get_followup_prompt(intent)
            else:
                # Mock response - in real app, call /outlets API
                return f"Ah yes, the {self.slots['current_outlet']} outlet opens at 9:00AM."
        elif intent == "opening_time" and self.slots["current_outlet"]:
            return f"Ah yes, the {self.slots['current_outlet']} outlet opens at 9:00AM."
        else:
            # Fallback to LLM with memory
            prompt = f"User: {user_input}\nBot: "
            messages = self.memory.load_memory_variables({})
            history = messages.get("history", [])
            full_prompt = f"Conversation History:\n{history}\n\n{prompt}"
            response = self.llm.invoke(full_prompt)
            self.memory.save_context({"input": user_input}, {"output": response.content})
            return response.content

    def reset(self):
        """Reset conversation state"""
        self.memory.clear()
        self.slots = {
            "current_city": None,
            "current_outlet": None,
            "last_intent": None
        }
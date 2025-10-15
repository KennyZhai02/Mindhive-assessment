An intelligent conversational assistant

Find outlet locations, hours, and services
Discover drinkware products (tumblers, mugs, accessories)
Perform simple calculations
Maintain contextual, multi-turn conversations
Built with FastAPI, LangChain, and a modular agent-based architecture—designed for reliability, security, and ease of deployment.

Setup & Run Instructions
Prerequisites
Python 3.9+
pip package manager
(Optional) OpenAI API Key

pip install -r requirements.txt

Set Environment Variables (Optional)
Create a .env file in the project root:
OPENAI_API_KEY=your_openai_api_key_here
MOCK_MODE=false
Set MOCK_MODE=true to disable all OpenAI calls and use built-in mock responses.
Without an API key, the system automatically falls back to mock mode.


Prepare Data Sources
Scrape & Build Product Knowledge Base
python scrape_products.py
python build_product_vectorstore.py

Scrapes drinkware from shop.zuscoffee.com
Generates data/drinkware.jsonl
Builds FAISS vector store at vectorstore/product_kb/
Fallback: If scraping fails, uses curated sample products (12+ items). 

Scrape & Create Outlet Database
python scrape_outlets.py        # → saves data/outlets.csv
python create_outlets_db.py     # → creates data/outlets.db (SQLite)
Gathers real outlet info from ZUS website
Falls back to 15+ known Malaysian locations if scraping fails

Launch the Application
python -m pytest test_*.py -v

Includes:
Integration tests: /outlets, /products, /calculate
Security tests: SQLi, XSS, code injection, path traversal
Unhappy flow tests: empty inputs, API downtime, malformed responses
Agent & planner logic: intent parsing, slot filling, context switching

Acknowledgements
Built for the Mindhive Assessment
Uses real ZUS Coffee product & outlet data (with fallbacks)
Powered by LangChain, FAISS, and FastAPI

Architecture Overview
Key Components
Web Interface (templates/index.html): A responsive chat UI with quick-action buttons and typing indicators.
FastAPI Server (main.py): Exposes /chat, /products, /outlets, and /calculate endpoints with input validation and error handling.
ConversationAgent (chatbot/agent.py): Manages conversation state using slots (e.g., current_outlet), parses user intent, plans actions, and executes tools.
Tools (chatbot/tools.py): Encapsulate domain logic:
CalculatorTool: Uses regex validation and sandboxed eval() for safe math.
ProductRAGTool: Queries a FAISS vector store and uses an LLM to generate answers from retrieved context.
OutletSQLTool: In real mode, uses an LLM to generate SQL; in mock mode, falls back to keyword search.
Data Ingestion: Scrapes and structures product/outlet data into standardized formats.
Storage: FAISS for product embeddings, SQLite for outlet data.

Data Flow
User sends a message via the web UI → /chat endpoint.
The ConversationAgent updates slots (e.g., detects “SS 2” → sets current_outlet).
Intent is parsed using keyword and regex rules—no LLM for simple cases.
The agent plans an action (execute_calculator, ask_outlet, etc.).
The appropriate tool is executed:
Calculator validates and evaluates the expression securely.
Products queries FAISS and generates an LLM answer (or mock response).
Outlets either runs LLM-generated SQL (real mode) or keyword search (mock mode).
A natural-language response is returned to the user.

Key Trade-offs & Decisions
Hybrid Intent Parsing: Avoids LLM latency and cost for common intents like calculation or outlet lookup.
Mock Mode by Default: Ensures the system is fully functional without internet or OpenAI credits—critical for assessments.
SQLite for Outlets: Lightweight, serverless, and sufficient for read-only queries.
FAISS for Product Search: Enables fast, local semantic search without external vector databases.
Sandboxed Math Evaluation: Safe execution of expressions without external services.
Stateful Slots: Tracks context (e.g., current outlet) without storing full conversation history.
No Authentication: Keeps scope focused on core assistant functionality.


Security Measures
SQL Injection Protection: LLM-generated SQL is validated; dangerous keywords (DROP, DELETE, etc.) are blocked.
Code Injection Prevention: Calculator rejects non-math characters and disables built-ins.
XSS Protection: Web UI uses textContent instead of innerHTML to prevent script injection.
Input Validation: FastAPI enforces min_length=1 on all query parameters.
Error Isolation: Tools return structured errors; the agent never crashes.

Acknowledgements
Built for the Mindhive Assessment
Powered by LangChain, FAISS, and FastAPI
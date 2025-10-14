# Mindhive-assessment

A multi-turn conversational AI assistant for ZUS Coffee that demonstrates agentic planning, tool integration, RAG (Retrieval-Augmented Generation), and Text2SQL capabilities.

Heroku Demo: 

Table of Contents

Features
Architecture
Setup & Installation
API Documentation
Testing
Deployment
Project Structure
Key Design Decisions

Features:

Part 1: Sequential Conversation 

Multi-turn context tracking with conversation memory
Slot-based state management for city, outlet, and user intents
Interrupted flow handling with graceful context switching

Part 2: Agentic Planning 

Intent parsing from natural language
Action selection logic (ask, call tool, or finish)
Dynamic response generation based on conversation state

Part 3: Tool Calling 

Calculator API with arithmetic expression evaluation
Error handling for invalid expressions and edge cases
Graceful degradation on API failures

Part 4: Custom API & RAG Integration 
Product RAG Endpoint

Vector store using FAISS for product embeddings
Semantic search over ZUS drinkware catalog
AI-generated summaries using GPT-3.5-turbo

Outlets Text2SQL Endpoint

Natural language to SQL translation
SQLite database with outlet information
Secure query execution with SQL injection prevention

Part 5: Unhappy Flows 

Missing parameters handling with helpful prompts
API downtime simulation and graceful fallbacks
Malicious payload protection (SQL injection, XSS, code injection)
Comprehensive error messages and recovery suggestions

Setup & Installation
Prerequisites

Python 3.11+
OpenAI API Key
Git

Install dependencies
pip install -r requirements.txt
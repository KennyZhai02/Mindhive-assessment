from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import create_engine, text
import re
import os

# Import the agent for chat interface
from chatbot.agent import ConversationAgent

app = FastAPI(title="Mindhive Assessment API")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Global agent instance for chat sessions (in production, use session management)
chat_agent = None

def get_agent():
    global chat_agent
    if chat_agent is None:
        chat_agent = ConversationAgent()
    return chat_agent

# --- Web Interface ---
@app.get("/", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Serve the chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})

class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat(msg: ChatMessage):
    """Handle chat messages from the web interface"""
    try:
        agent = get_agent()
        response = agent.process_turn(msg.message)
        return {"response": response}
    except Exception as e:
        return {"response": f"I apologize, but I encountered an error: {str(e)}"}

@app.post("/chat/reset")
async def reset_chat():
    """Reset the chat session"""
    global chat_agent
    if chat_agent:
        chat_agent.reset()
    return {"status": "Chat session reset"}

# --- Part 3: Calculator ---
class CalculateRequest(BaseModel):
    expr: str

@app.post("/calculate")
async def calculate(request: CalculateRequest):
    """
    Calculate mathematical expressions.
    Supports: +, -, *, /, parentheses
    
    Example: {"expr": "5 * 6"}
    """
    expr = request.expr
    
    # Security: Only allow safe mathematical characters
    if not re.match(r'^[\d+\-*/().\s]+$', expr):
        raise HTTPException(status_code=400, detail="Invalid characters in expression. Only numbers and +, -, *, /, () are allowed.")
    
    try:
        # Evaluate safely (no access to builtins)
        result = eval(expr, {"__builtins__": {}}, {})
        return {"result": result, "expression": expr}
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")

# --- Part 4: Product RAG ---
@app.get("/products")
async def search_products(query: str = Query(..., min_length=1, description="Search query for products")):
    """
    Search ZUS Coffee products using RAG (Retrieval-Augmented Generation).
    
    Returns AI-generated answers based on product knowledge base.
    
    Example: /products?query=What tumblers do you have?
    """
    try:
        vectorstore_path = "vectorstore/product_kb"
        
        if not os.path.exists(vectorstore_path):
            raise HTTPException(
                status_code=500, 
                detail="Product knowledge base not initialized. Run: python ingest/build_product_vectorstore.py"
            )
        
        # Load vector store
        vectorstore = FAISS.load_local(
            vectorstore_path, 
            OpenAIEmbeddings(), 
            allow_dangerous_deserialization=True
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # Retrieve relevant documents
        docs = retriever.invoke(query)
        
        if not docs:
            return {
                "answer": "I couldn't find any relevant product information. Please try a different query.",
                "sources": []
            }
        
        # Build context from documents
        context = "\n".join([d.page_content for d in docs])
        
        # Generate answer using LLM
        prompt = PromptTemplate.from_template(
            """You are a helpful ZUS Coffee product assistant. Answer the question based on the context provided.
            
Context:
{context}

Question: {question}

Answer: Provide a helpful, friendly response about ZUS Coffee products."""
        )
        
        chain = prompt | ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3) | StrOutputParser()
        answer = chain.invoke({"context": context, "question": query})
        
        return {
            "answer": answer,
            "sources": [
                {
                    "title": d.metadata.get("title", "Unknown"), 
                    "price": d.metadata.get("price", "N/A")
                } 
                for d in docs
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")

# --- Part 4: Outlets Text2SQL ---
@app.get("/outlets")
async def search_outlets(query: str = Query(..., min_length=1, description="Natural language query for outlets")):
    """
    Search ZUS Coffee outlets using Text-to-SQL.
    
    Converts natural language queries to SQL and executes them safely.
    
    Example: /outlets?query=outlets in Petaling Jaya
    """
    try:
        db_path = "data/outlets.db"
        
        if not os.path.exists(db_path):
            raise HTTPException(
                status_code=500, 
                detail="Outlet database not initialized. Run: python ingest/create_outlets_db.py"
            )
        
        # Create database engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.connect() as conn:
            # Generate SQL query using LLM
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
            
            prompt = f"""Convert this natural language query to SQL for the 'outlets' table.
            
Table schema:
- outlets (name TEXT, address TEXT, opening_hours TEXT, services TEXT)

Query: "{query}"

Return ONLY the SQL SELECT statement, nothing else. Use LIKE for text matching.
Example: SELECT * FROM outlets WHERE name LIKE '%SS 2%' OR address LIKE '%SS 2%'"""
            
            sql_query = llm.invoke(prompt).content.strip()
            
            # Remove markdown code blocks if present
            sql_query = re.sub(r'```sql\s*|\s*```', '', sql_query).strip()
            
            # Security: Strict SQL validation
            if not sql_query.upper().startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed")
            
            # Block dangerous SQL keywords
            dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE", "EXEC", "--", ";"]
            sql_upper = sql_query.upper()
            
            for keyword in dangerous_keywords:
                if keyword in sql_upper and keyword != "SELECT":
                    raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
            
            # Execute query
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result]
            
            return {
                "results": rows,
                "query": query,
                "sql": sql_query,
                "count": len(rows)
            }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text2SQL error: {str(e)}")

# --- Health Check ---
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "product_kb_exists": os.path.exists("vectorstore/product_kb"),
        "outlet_db_exists": os.path.exists("data/outlets.db")
    }

# --- API Documentation Override ---
@app.get("/api/docs", include_in_schema=False)
async def custom_docs():
    """Custom API documentation"""
    return {
        "title": "ZUS Coffee AI Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "/": "Chat interface (Web UI)",
            "/chat": "POST - Send chat message",
            "/calculate": "POST - Calculate mathematical expressions",
            "/products": "GET - Search products using RAG",
            "/outlets": "GET - Search outlets using Text2SQL",
            "/health": "GET - Health check"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
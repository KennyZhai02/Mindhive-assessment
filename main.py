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

# Mock mode for demo without OpenAI credits
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# Global agent instance
chat_agent = None

def get_agent():
    global chat_agent
    if chat_agent is None:
        chat_agent = ConversationAgent()
    return chat_agent

# Mock responses database
MOCK_PRODUCT_RESPONSES = {
    "tumbler": "We offer several great tumbler options! The **OG CUP 2.0** (RM 49.90) features a screw-on lid and double-wall insulation. The **All-Can Tumbler** (RM 59.90) is versatile and fits standard cans. The **All Day Cup** (RM 49.90) is perfect for daily use with ergonomic design.",
    "mug": "We have two excellent mug options: The **OG Ceramic Mug** (RM 39.90) is microwave and dishwasher safe, perfect for your morning coffee. The **ZUS Stainless Steel Mug** (RM 44.90) features double-wall insulation to keep drinks hot or cold.",
    "og cup": "The **OG CUP 2.0** (RM 49.90) is our iconic tumbler with an upgrade! It features a screw-on lid for secure transport and double-wall insulation to keep your drinks at the perfect temperature. 500ml capacity (17oz).",
    "price": "Our drinkware prices range from RM 39.90 to RM 59.90. Ceramic mugs start at RM 39.90, standard tumblers at RM 49.90, and premium tumblers at RM 59.90. All products feature quality materials and excellent insulation.",
    "default": "We offer a wide range of drinkware including tumblers (RM 49.90-59.90), mugs (RM 39.90-44.90), and accessories. Our products feature quality insulation and Malaysian-inspired designs. What specific product are you interested in?"
}

MOCK_OUTLET_DATA = {
    "ss 2": {"name": "ZUS Coffee - SS 2", "address": "No. 75, Jalan SS 2/67, SS 2, 47300 Petaling Jaya, Selangor", "opening_hours": "8:00 AM - 10:00 PM", "services": "Dine-in, Takeaway, Delivery, Drive-thru"},
    "bangsar": {"name": "ZUS Coffee - Bangsar", "address": "No. 11, Jalan Telawi 3, Bangsar Baru, 59100 Kuala Lumpur", "opening_hours": "7:00 AM - 11:00 PM", "services": "Dine-in, Takeaway, Delivery"},
    "klcc": {"name": "ZUS Coffee - KLCC", "address": "Lot 241, Level 2, Suria KLCC, 50088 Kuala Lumpur", "opening_hours": "9:00 AM - 10:00 PM", "services": "Dine-in, Takeaway"},
}

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
    """Calculate mathematical expressions - no OpenAI needed"""
    expr = request.expr
    
    if not re.match(r'^[\d+\-*/().\s]+$', expr):
        raise HTTPException(status_code=400, detail="Invalid characters in expression")
    
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return {"result": result, "expression": expr}
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")

# --- Part 4: Product RAG ---
@app.get("/products")
async def search_products(query: str = Query(..., min_length=1)):
    """Search ZUS Coffee products using RAG (or mock mode)"""
    
    if MOCK_MODE:
        # Mock response without calling OpenAI
        query_lower = query.lower()
        
        # Find best matching response
        if "tumbler" in query_lower:
            answer = MOCK_PRODUCT_RESPONSES["tumbler"]
            sources = [
                {"title": "OG CUP 2.0", "price": "RM 49.90"},
                {"title": "All-Can Tumbler", "price": "RM 59.90"},
                {"title": "All Day Cup", "price": "RM 49.90"}
            ]
        elif "mug" in query_lower:
            answer = MOCK_PRODUCT_RESPONSES["mug"]
            sources = [
                {"title": "OG Ceramic Mug", "price": "RM 39.90"},
                {"title": "ZUS Stainless Steel Mug", "price": "RM 44.90"}
            ]
        elif "og" in query_lower or "og cup" in query_lower:
            answer = MOCK_PRODUCT_RESPONSES["og cup"]
            sources = [{"title": "OG CUP 2.0", "price": "RM 49.90"}]
        elif "price" in query_lower or "cost" in query_lower or "how much" in query_lower:
            answer = MOCK_PRODUCT_RESPONSES["price"]
            sources = [
                {"title": "Various Products", "price": "RM 39.90 - 59.90"}
            ]
        else:
            answer = MOCK_PRODUCT_RESPONSES["default"]
            sources = [
                {"title": "Drinkware Collection", "price": "Various"}
            ]
        
        return {"answer": answer, "sources": sources, "mock_mode": True}
    
    try:
        vectorstore_path = "vectorstore/product_kb"
        
        if not os.path.exists(vectorstore_path):
            raise HTTPException(status_code=500, detail="Product KB not initialized")
        
        vectorstore = FAISS.load_local(vectorstore_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(query)
        
        if not docs:
            return {"answer": "I couldn't find relevant product information.", "sources": []}
        
        context = "\n".join([d.page_content for d in docs])
        prompt = PromptTemplate.from_template(
            "Answer based on context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        )
        
        chain = prompt | ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3) | StrOutputParser()
        answer = chain.invoke({"context": context, "question": query})
        
        return {
            "answer": answer,
            "sources": [{"title": d.metadata.get("title"), "price": d.metadata.get("price")} for d in docs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")

# --- Part 4: Outlets Text2SQL ---
@app.get("/outlets")
async def search_outlets(query: str = Query(..., min_length=1)):
    """Search ZUS Coffee outlets using Text2SQL (or mock mode)"""
    
    if MOCK_MODE:
        # Direct SQL search without LLM
        try:
            db_path = "data/outlets.db"
            if not os.path.exists(db_path):
                # Return mock data
                query_lower = query.lower()
                results = []
                
                for key, outlet in MOCK_OUTLET_DATA.items():
                    if key in query_lower or query_lower in outlet["address"].lower():
                        results.append(outlet)
                
                if not results:
                    # Search all if no match
                    results = list(MOCK_OUTLET_DATA.values())[:3]
                
                return {"results": results, "count": len(results), "mock_mode": True}
            
            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                # Simple keyword search
                sql = text("""
                    SELECT * FROM outlets 
                    WHERE name LIKE :query 
                    OR address LIKE :query
                    LIMIT 5
                """)
                result = conn.execute(sql, {"query": f"%{query}%"})
                rows = [dict(row._mapping) for row in result]
                
                if not rows:
                    return {"results": [], "count": 0, "message": "No outlets found"}
                
                return {"results": rows, "count": len(rows), "mock_mode": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    try:
        db_path = "data/outlets.db"
        if not os.path.exists(db_path):
            raise HTTPException(status_code=500, detail="Outlet DB not initialized")
        
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.connect() as conn:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
            
            prompt = f"""Convert to SQL for 'outlets' table (columns: name, address, opening_hours, services).
Query: "{query}"
Return ONLY the SQL SELECT statement."""
            
            sql_query = llm.invoke(prompt).content.strip()
            sql_query = re.sub(r'```sql\s*|\s*```', '', sql_query).strip()
            
            if not sql_query.upper().startswith("SELECT"):
                raise ValueError("Only SELECT allowed")
            
            dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE", "EXEC"]
            if any(kw in sql_query.upper() for kw in dangerous):
                raise ValueError("Malicious SQL detected")
            
            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result]
            
            return {"results": rows, "query": query, "sql": sql_query, "count": len(rows)}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text2SQL error: {str(e)}")

# --- Health Check ---
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mock_mode": MOCK_MODE,
        "product_kb_exists": os.path.exists("vectorstore/product_kb"),
        "outlet_db_exists": os.path.exists("data/outlets.db")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
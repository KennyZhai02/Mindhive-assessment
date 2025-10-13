from fastapi import FastAPI, HTTPException, Query
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import create_engine, text
import re
import os

app = FastAPI(title="Mindhive Assessment API")

# --- Part 3: Calculator ---
@app.post("/calculate")
async def calculate(expr: str):
    if not re.match(r'^[\d+\-*/().\s]+$', expr):
        raise HTTPException(status_code=400, detail="Invalid characters in expression")
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return {"result": result}
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")

# --- Part 4: Product RAG ---
@app.get("/products")
async def search_products(query: str = Query(..., min_length=1)):
    try:
        if not os.path.exists("vectorstore/product_kb"):
            raise HTTPException(status_code=500, detail="Product KB not initialized")
        vectorstore = FAISS.load_local("vectorstore/product_kb", OpenAIEmbeddings(), allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(query)

        context = "\n".join([d.page_content for d in docs])
        prompt = PromptTemplate.from_template(
            "Answer based on context:\n{context}\n\nQuestion: {question}"
        )
        chain = prompt | ChatOpenAI(model="gpt-3.5-turbo") | StrOutputParser()
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
    try:
        if not os.path.exists("data/outlets.db"):
            raise HTTPException(status_code=500, detail="Outlet DB not initialized")
        engine = create_engine("sqlite:///data/outlets.db")
        with engine.connect() as conn:
            llm = ChatOpenAI(model="gpt-3.5-turbo")
            prompt = f"""Convert to SQL for 'outlets' table (columns: name, address, opening_hours, services). Return ONLY SQL.
Query: "{query}" """
            sql_query = llm.invoke(prompt).content.strip()

            # Security: validate SQL
            if not sql_query.upper().startswith("SELECT"):
                raise ValueError("Only SELECT allowed")
            dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER"]
            if any(kw in sql_query.upper() for kw in dangerous):
                raise ValueError("Malicious SQL detected")

            result = conn.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result]
            return {"results": rows}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text2SQL error: {str(e)}")
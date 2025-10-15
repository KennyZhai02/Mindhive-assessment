from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import json

def build_product_vectorstore():
    docs = []
    with open("data/drinkware.jsonl", "r", encoding="utf-8") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            if line:  
                try:
                    json_obj = json.loads(line)
                    
                    doc = Document(
                        page_content=f"{json_obj.get('title', '')} - {json_obj.get('description', '')}",
                        metadata={
                            "title": json_obj.get("title"),
                            "price": json_obj.get("price"),
                            "url": json_obj.get("url")
                        }
                    )
                    docs.append(doc)
                except json.JSONDecodeError as e:
                    print(f"Warning: Error parsing JSON on line {line_num}: {e}")
                    print(f"  Content: {line[:100]}...") 

    if not docs:
        print("No valid documents were loaded from the JSONL file.")
        return


    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local("vectorstore/product_kb")
    print(" Product vector store built and saved.")

if __name__ == "__main__":
    build_product_vectorstore()
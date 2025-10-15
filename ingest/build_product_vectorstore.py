from langchain_community.document_loaders import JSONLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import os
import sys

def build_product_vectorstore():
    """
    Build product vector store from scraped data.
    Skips if OPENAI_API_KEY is not available or MOCK_MODE is enabled.
    """
    
    # Check if we should skip vector store building
    mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if mock_mode:
        print("MOCK_MODE enabled - Skipping vector store build")
        print("✓  Mock mode will use keyword-based product search")
        return
    
    if not api_key:
        print("OPENAI_API_KEY not found - Skipping vector store build")
        print("✓  Set OPENAI_API_KEY environment variable to build vector store")
        print("✓  Or enable MOCK_MODE for demo without OpenAI")
        return
    
    # Check if data file exists
    if not os.path.exists("data/drinkware.jsonl"):
        print("Error: data/drinkware.jsonl not found")
        print("   Run: python ingest/scrape_products.py")
        sys.exit(1)
    
    try:
        print("Building product vector store...")
        
        # Load documents
        loader = JSONLoader(
            file_path="data/drinkware.jsonl",
            jq_schema=".title + ' - ' + .description",
            text_content=False
        )
        docs = loader.load()
        
        print(f"   Loaded {len(docs)} products")
        
        # Process documents
        processed_docs = []
        for doc in docs:
            if hasattr(doc, 'page_content') and isinstance(doc.page_content, dict):
                content = doc.page_content
                text = f"{content.get('title', '')} - {content.get('description', '')}"
                processed_docs.append(
                    Document(
                        page_content=text,
                        metadata={
                            "title": content.get("title", "Unknown"),
                            "price": content.get("price", "N/A")
                        }
                    )
                )
            else:
                text = str(doc.page_content)
                processed_docs.append(
                    Document(
                        page_content=text,
                        metadata=getattr(doc, 'metadata', {})
                    )
                )
        
        print(f"   Processed {len(processed_docs)} documents")
        
        print("   Creating embeddings (this may take a minute)...")
        embeddings = OpenAIEmbeddings()
        
        vectorstore = FAISS.from_documents(processed_docs, embeddings)
        
        os.makedirs("vectorstore", exist_ok=True)
        vectorstore.save_local("vectorstore/product_kb")
        
        print("Product vector store built and saved to vectorstore/product_kb")
        
    except Exception as e:
        print(f"Error building vector store: {str(e)}")
        print("This is okay if you're using MOCK_MODE")
        print("To use full AI features, ensure OPENAI_API_KEY is set and has credits")
        return

if __name__ == "__main__":
    build_product_vectorstore()
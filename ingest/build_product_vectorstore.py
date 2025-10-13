from langchain_community.document_loaders import JSONLLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

def build_product_vectorstore():
    loader = JSONLLoader("data/drinkware.jsonl")
    docs = loader.load()

    processed_docs = [
        Document(
            page_content=f"{doc.page_content.get('title', '')} - {doc.page_content.get('description', '')}",
            metadata={"title": doc.page_content.get("title"), "price": doc.page_content.get("price")}
        )
        for doc in docs
    ]

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(processed_docs, embeddings)
    vectorstore.save_local("vectorstore/product_kb")
    print(" Product vector store built and saved.")

if __name__ == "__main__":
    build_product_vectorstore()
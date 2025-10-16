# ---------------- IMPORTS ----------------
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from pathlib import Path
import os
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv(dotenv_path="./.env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GOOGLE_API_KEY or not GROQ_API_KEY:
    raise SystemExit("Missing API keys in .env file")

# ---------------- CONFIG ----------------
DOCS_PATH = Path("./my_docs")          # Folder containing dataset files
INDEX_PATH = Path("./faiss_index")     # Folder to store FAISS index
REBUILD_INDEX = True                    # Rebuild index from dataset
EMBED_MODEL = "models/embedding-001"   # Gemini embedding model
CHAT_MODEL = "llama-3.3-70b-versatile" # Groq LLaMA chat model
TOP_K = 4                               # Number of chunks to retrieve
SEARCH_TYPE = "mmr"                     # "mmr" or "similarity"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# ---------------- HELPER FUNCTIONS ----------------
def find_files(path: Path) -> list[Path]:
    """Find all CSV or TXT files in the given path"""
    if path.is_file():
        return [path]
    exts = [".csv", ".txt"]
    return [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in exts]

def load_documents(paths: list[Path]) -> list[Document]:
    """Load CSV or TXT documents"""
    docs = []
    for p in paths:
        try:
            if p.suffix.lower() == ".csv":
                docs.extend(CSVLoader(str(p)).load())
            elif p.suffix.lower() == ".txt":
                docs.extend(TextLoader(str(p), encoding="utf-8").load())
        except Exception as e:
            print(f"[WARN] Failed to load {p}: {e}")
    return docs

def split_documents(docs: list[Document]) -> list[Document]:
    """Split documents into smaller chunks for embeddings"""
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_documents(docs)

def build_or_load_faiss(chunks: list[Document], rebuild: bool) -> FAISS:
    """Build or load FAISS vector store"""
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
    if rebuild:
        print("Building FAISS index from dataset...")
        vs = FAISS.from_documents(chunks, embeddings)
        INDEX_PATH.mkdir(parents=True, exist_ok=True)
        vs.save_local(str(INDEX_PATH))
        print(f"FAISS index saved to: {INDEX_PATH.resolve()}")
    print(f"Loading FAISS index from: {INDEX_PATH.resolve()}")
    vs = FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
    return vs

def make_retriever(vectorstore: FAISS):
    """Create retriever from FAISS"""
    return vectorstore.as_retriever(search_type=SEARCH_TYPE, search_kwargs={"k": TOP_K})

def make_rag_chain(retriever):
    """Create RAG chain using Groq LLaMA"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a concise assistant. Answer only from the dataset context and cite sources."),
        ("human", "Question:\n{input}\n\nContext:\n{context}")
    ])
    llm = ChatGroq(model=CHAT_MODEL, temperature=0.2)
    doc_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, doc_chain)

def format_sources(ctx: list[Document]) -> str:
    """Pretty-print sources without duplicates"""
    sources = [d.metadata.get("source") or d.metadata.get("file_path") or "unknown" for d in ctx]
    sources = list(set(sources))  # deduplicate
    return ", ".join(sources)

# ---------------- MAIN WORKFLOW ----------------
def main():
    chunks = []
    if REBUILD_INDEX:
        files = find_files(DOCS_PATH)
        if not files:
            raise SystemExit("No documents found in my_docs folder")
        print(f"Found {len(files)} files. Loading documents...")
        docs = load_documents(files)
        print(f"Splitting documents into chunks...")
        chunks = split_documents(docs)

    vectorstore = build_or_load_faiss(chunks, rebuild=REBUILD_INDEX)
    retriever = make_retriever(vectorstore)
    rag_chain = make_rag_chain(retriever)

    questions_map = {
        '1': {
            'name': 'Product-based Questions',
            'questions': [
                "What is the price of Apple iPhone 15?",
                "What is the discount on Samsung Galaxy S23?",
                "Which source sells Dell XPS 13?",
                "What category does Sony WH-1000XM5 belong to?",
                "Which products are available on Flipkart?",
                "Which products are available on Amazon?",
                "Which products are available on Myntra?",
            ]
        },
        '2': {
            'name': 'Category-based Questions',
            'questions': [
                "List all laptops and their prices.",
                "Show all electronics with more than 10% discount.",
                "Which cameras are listed in the file?",
                "What are the available wearables and their prices?",
                "List all accessories with a discount greater than 10%.",
            ]
        },
        '3': {
            'name': 'Pricing and Discount-based Questions',
            'questions': [
                "Which product has the highest price?",
                "Which product has the lowest price?",
                "Which product has the highest discount?",
                "Which products have a discount of 20%?",
                "List all products with a discount of 15% or more.",
                "Which laptops have a discount of 10%?",
            ]
        },
        '4': {
            'name': 'Source-based Questions',
            'questions': [
                "Which products are sold on Amazon?",
                "Which products are sold on Flipkart?",
                "Which products are sold on Myntra?",
                "Which cameras are available on Amazon?",
                "Which wearables are available on Flipkart?",
            ]
        },
        '5': {
            'name': 'Comparison Questions',
            'questions': [
                "Compare the prices of Apple MacBook Air and HP Spectre x360.",
                "Which is cheaper: Fitbit Charge 6 or Garmin Forerunner 955?",
                "Which has a higher discount: JBL Charge 5 or Sony WH-1000XM5?",
            ]
        },
        '6': {
            'name': 'General Questions',
            'questions': [
                "How many products are listed in the file?",
                "What categories are present in the file?",
                "List all drones and their prices.",
                "Which products have a price less than 10,000?",
                "Which products have a price greater than 100,000?",
            ]
        },
        '7': {
            'name': 'Advanced Questions',
            'questions': [
                "Which product has the highest discount in the Accessories category?",
                "List all products in the Laptops category with a discount of 8%.",
                "Which electronics are available for less than 20,000?",
                "Are there any products with a 5% discount?",
                "Which products are available in more than one category? (if any)",
            ]
        }
    }
    print("Type 'exit' to quit.")
    
    current_category_choice = None

    while True:
        if current_category_choice is None:
            print("\nChoose category:")
            for key, value in questions_map.items():
                print(f"{key}. {value['name']}")
            print("Or type 'exit' to quit.")
            category_choice = input("Enter your choice: ")
        else:
            category_choice = current_category_choice

        if category_choice.lower() in ("exit", "quit"):
            break

        if category_choice in questions_map:
            current_category_choice = category_choice
            category = questions_map[category_choice]
            print(f"\n--- {category['name']} ---")
            for i, q in enumerate(category['questions']):
                print(f"{i+1}. {q}")
            
            question_choice = input("\nSelect a question number or type 'back' to choose another category: ")
            if question_choice.lower() == 'back':
                current_category_choice = None
                continue
            
            try:
                question_index = int(question_choice) - 1
                if 0 <= question_index < len(category['questions']):
                    query = category['questions'][question_index]
                    print(f"\nYour question: {query}")
                    
                    result = rag_chain.invoke({"input": query})
                    answer = result.get("answer") or result.get("output") or str(result)
                    print("\nRAG Answer:", answer.strip())
                    
                    ctx = result.get("context", [])
                    if ctx:
                        print("Sources:", format_sources(ctx))

                #-------------looping for questions-----------------
                    while True:
                        continue_choice = input("\nDo you want to continue (yes/no)? ").lower()
                        if continue_choice == 'no':
                            print("Thank you.👋")
                            return
                        elif continue_choice == 'yes':
                            same_category = input("Do you want to continue with the same category (yes/no)? ").lower()
                            if same_category == 'yes':
                                # Loop back to the question selection for the same category
                                break
                            elif same_category == 'no':
                                # Reset current_category_choice to display the main menu
                                current_category_choice = None
                                break
                            else:
                                print("Invalid choice. Please enter 'yes' or 'no'.")
                        else:
                            print("Invalid choice. Please enter 'yes' or 'no'.")
                else:
                    print("Invalid question number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        else:
            print("Invalid category choice. Please try again.")

if __name__ == "__main__":
    main() 
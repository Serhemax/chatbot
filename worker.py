import os
from langchain_ollama import ChatOllama
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from collections import defaultdict

# Store a mapping of conversation IDs to chat history, vector stores, and document sources
conversation_data = defaultdict(lambda: {"history": [], "vector_stores": [], "document_sources": []})

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize global variables
llm = None
llm_embeddings = None

# Function to initialize the language model and its embeddings
def init_llm():
    global llm, llm_embeddings
    model_name = "llama3:8b"
    llm = ChatOllama(model=model_name)
    llm_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Function to process a PDF document
def process_document(document_path, conversation_id="default"):
    global llm, llm_embeddings
    # Extract document name from the path
    document_name = os.path.basename(document_path)
    
    # Load the document
    loader = PyPDFLoader(document_path)
    documents = loader.load()
    
    # Add metadata (document name) to each chunk
    for doc in documents:
        doc.metadata["source"] = document_name
    
    # Split the document into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    
    # Create a vector store with the metadata
    db = Chroma.from_documents(texts, llm_embeddings, persist_directory='./docs/chroma')
    
    # Append the new vector store and document name to the conversation data
    conversation_data[conversation_id]["vector_stores"].append(db)
    conversation_data[conversation_id]["document_sources"].append(document_name)

# Function to process a user prompt
def process_prompt(prompt, conversation_id="default"):
    global llm
    # Get the conversation data for the specific ID
    conversation = conversation_data[conversation_id]
    vector_stores = conversation["vector_stores"]
    document_sources = conversation["document_sources"]

    if not vector_stores:
        return "No documents in memory. Please upload a PDF first."

    # Combine all retrievers from the vector stores
    retrievers = [db.as_retriever(search_type="similarity", search_kwargs={"k": 2}) for db in vector_stores]
    # Aggregate responses from all retrievers
    answers = []
    sources = []

    for retriever, doc_source in zip(retrievers, document_sources):
        chain = ConversationalRetrievalChain.from_llm(llm, retriever)
        result = chain({"question": prompt, "chat_history": conversation["history"]})
        answers.append(result["answer"])
        sources.append(doc_source)

    # Combine answers and update chat history
    combined_answer = " ".join(answers)
    citation = f"\n\nInformation taken from: {', '.join(sources)}"
    combined_answer_with_citation = combined_answer + citation

    conversation["history"].append((prompt, combined_answer_with_citation))

    return combined_answer_with_citation


# Initialize the language model
init_llm()

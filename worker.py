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
    llm_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")

# Function to process a PDF document
def process_document(document_path, conversation_id="default"):
    global llm, llm_embeddings
    # Extract document name from the path
    document_name = os.path.basename(document_path)
    if document_name in conversation_data[conversation_id]["document_sources"]:
        print(f"Document '{document_name}' is already processed.")
        return {"status": "error", "message": f"Document '{document_name}' already exists."}

    # Load the document
    loader = PyPDFLoader(document_path)
    documents = loader.load()
    
    # Add metadata (document name) to each chunk
    for doc in documents:
        if "page" not in doc.metadata:
            doc.metadata["page"] = "Unknown"
        doc.metadata["source"] = document_name

    
    # Split the document into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    
    print("Indexed Chunks:")
    for i, chunk in enumerate(texts):
        print(f"Chunk {i}: {chunk.page_content[:100]}...")  # Log the first 20 characters of each chunk

    # Create a vector store with the metadata
    persist_dir = ".db/"
    os.makedirs(persist_dir, exist_ok=True)
    db = Chroma.from_documents(
        texts, llm_embeddings, persist_directory=persist_dir
    )

    # Append the new vector store and document name to the conversation data
    conversation_data[conversation_id]["vector_stores"].append(db)
    conversation_data[conversation_id]["document_sources"].append(document_name)

# Function to process a user prompt
def process_prompt(prompt, conversation_id="default"):
    global llm
    conversation = conversation_data[conversation_id]
    vector_stores = conversation["vector_stores"]
    document_sources = conversation["document_sources"]

    if not vector_stores:
        return "No documents in memory. Please upload a PDF first."

    # Combine all retrievers from the vector stores
    retrievers = [db.as_retriever(search_type="similarity", search_kwargs={"k": 5}) for db in vector_stores]
    
    print("Retrieved Chunks:")
    answers = []
    sources = []

    for retriever, doc_source in zip(retrievers, document_sources):
        chain = ConversationalRetrievalChain.from_llm(llm, retriever)
        result = chain.invoke({"question": prompt, "chat_history": conversation["history"]})
        answers.append(result["answer"])
        sources.append(doc_source)
        print(f"Source: {doc_source}, Answer: {result['answer']}")

    # Check if no relevant answers were found
    if not any(answers):
        combined_answer = "I'm sorry, but I couldn't find relevant information based on the provided documents."
    else:
        combined_answer = " ".join(answers)
    
    sources = [src for src in document_sources if src in conversation_data[conversation_id]["document_sources"]]

    citation = f"\n\nInformation taken from: {', '.join(sources)}" if sources else ""
    combined_answer_with_citation = combined_answer + citation

    conversation["history"].append((prompt, combined_answer_with_citation))
    
    if not answers:  # If no answer is found
        all_text = " ".join([doc.page_content for doc in vector_stores[0]._texts])  # Access all text
        if prompt.lower() in all_text.lower():
            return "The requested information was found in the document but couldn't be retrieved effectively. Please refine your query."
        else:
            return "The requested information is not present in the document."

    return combined_answer_with_citation


def delete_file(file_name, conversation_id="default"):
    try:
        conversation = conversation_data[conversation_id]
        document_sources = conversation["document_sources"]

        # Check if the file exists in the document sources
        if file_name not in document_sources:
            return {"status": "error", "message": f"File '{file_name}' not found in the current conversation."}

         # Find and remove associated vector stores and metadata
        vector_stores = conversation["vector_stores"]
        for i, doc_source in enumerate(document_sources):
            if doc_source == file_name:
                del vector_stores[i]  # Remove vector store
                break

        document_sources.remove(file_name)  # Remove document source
        
        return {"status": "success", "message": f"File '{file_name}' successfully deleted."}

    except Exception as e:
        print(f"Error deleting file: {e}")
        return {"status": "error", "message": str(e)}




# Initialize the language model
init_llm()

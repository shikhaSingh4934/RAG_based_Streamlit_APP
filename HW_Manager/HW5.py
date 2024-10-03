import streamlit as st
import openai
import chromadb
from PyPDF2 import PdfReader
import docx 
# Ensure the API keys//
def run():
    openai.api_key = st.secrets["API_KEY"]
    # Function to generate embeddings for a given text
    def generate_embedding(text):
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response['data'][0]['embedding']

    # Function to create the ChromaDB collection and store it in session state
    def create_lab4_collection():
        client = chromadb.Client()
        collection = client.create_collection("Lab4Collection")
    
        return collection


    def handle_file_upload(uploaded_file):
        # Extract text from the uploaded file based on its type
        text = extract_text_from_file(uploaded_file)
        # Specify the folder containing PDF files
        if text:
            embedding = generate_embedding(text)
            if "Lab4_vectorDB" not in st.session_state:
                st.error("Lab4 vector database has not been initialized.")
                return
            
            collection = st.session_state.Lab4_vectorDB
            collection.add(
                documents=[text],
                ids=[uploaded_file.name],
                embeddings=[embedding]
            )
            st.success(f"File '{uploaded_file.name}' uploaded and processed successfully!")
        else:
            st.error("Failed to extract text from the uploaded file.")
    # Function to extract text from different file types

    def extract_text_from_file(uploaded_file):
        if uploaded_file.name.endswith(".pdf"):
            return extract_text_from_pdf(uploaded_file)
        
        elif uploaded_file.name.endswith(".txt"):
            return extract_text_from_txt(uploaded_file)

        elif uploaded_file.name.endswith(".docx"):
            return extract_text_from_docx(uploaded_file)

        else:
            st.error("Unsupported file type. Please upload a PDF, TXT, or DOCX file.")
            return None
        
    # Extract text from PDFs
    def extract_text_from_pdf(pdf_file):
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    # Extract text from TXT files
    def extract_text_from_txt(uploaded_file):
        return uploaded_file.read().decode('utf-8')

    # Extract text from DOCX files
    def extract_text_from_docx(uploaded_file):
        doc = docx.Document(uploaded_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text

    # Function to search the vector database for relevant documents
    def search_vectorDB(query):
        query_embedding = generate_embedding(query)

        # Ensure the collection exists in session state before querying
        if "Lab4_vectorDB" not in st.session_state:
            st.error("Lab4 vector database has not been initialized.")
            return None
        
        # Access the collection from session state
        collection = st.session_state.Lab4_vectorDB
        results = collection.query(query_embeddings=[query_embedding], n_results=3)
        
        if not results or len(results['documents']) == 0:
            return "No relevant documents found for your query."
        # Concatenate the retrieved documents
        documents = ""
        for i, doc in enumerate(results['documents'][0]):
            documents += f"Document {i+1}: {doc}\n"
        
        return documents

    # Function to generate a chatbot response using RAG (retrieval-augmented generation)
    def chatbot_response(query):
        # Step 1: Retrieve relevant documents from the vector database
        relevant_documents = search_vectorDB(query)
        

        if relevant_documents is None or relevant_documents.strip() == "":
            # If no relevant documents are found, return a general response
            use_rag = False
        else:
            # If relevant documents are found, use them in the prompt
            use_rag = True

        # Step 2: Combine the user query and relevant documents into a prompt for GPT
        conversation_history = [{"role": "system", "content": """
            You are a helpful assistant. After giving any response, always ask 'Do you want more info?'. 
            If the user says 'yes', provide additional details on the previous response. If the user says 'no', ask the user what else they would like help with. 
            If the user asks a new question, answer the new question and then ask 'Do you want more info?' again.
            Provide explanations in a way that a 10-year-old can understand.
        """}]

        # Include the relevant documents in the prompt if available
        if use_rag:
            conversation_history.append({
                "role": "system",
                "content": f"Relevant course information:\n{relevant_documents}"
            })

        # Add previous conversation history from session state
        conversation_history.extend(st.session_state.messages)

        # Add current user input to the conversation history
        conversation_history.append({"role": "user", "content": query})
        
        # Step 3: Send the prompt to GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )
        assistant_response = response['choices'][0]['message']['content']

        
        # Add assistant response to the conversation history in session state
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response


    #----------------------------MAIN---------------------------------

    # Initialize session state for messages if not already present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Check if Lab4_vectorDB is already initialized in session state
    if "Lab4_vectorDB" not in st.session_state:
        st.session_state.Lab4_vectorDB = create_lab4_collection()
        

    # Initialize the Lab4 vector database (ChromaDB collection) if not already created

    st.title("Course Information Chatbot")

    # File upload section
    uploaded_file = st.file_uploader("Upload a file (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"])
    if uploaded_file is not None:
        handle_file_upload(uploaded_file)

    # Display the full chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Always display the input box for user input
    prompt = st.chat_input("Ask anything")        

    if prompt:
        # Display user's message in the chat
        with st.chat_message("user"):
            st.markdown(prompt)

        # Save user's message to the session state
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate chatbot response using RAG
        assistant_response = chatbot_response(prompt)

        # Display the assistant's response in the chat
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

    
        

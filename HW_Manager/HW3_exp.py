import streamlit as st
import openai
import requests
import time
import anthropic
from bs4 import BeautifulSoup

def run():

    def read_url_content(url):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text()
        except requests.RequestException as e:
            st.error(f"Error reading {url}: {e}")
            return None

    # Sidebar for input of two URLs
    with st.sidebar:
        st.header("Input URLs")
        url1 = st.text_input("Enter the first URL:")
        url2 = st.text_input("Enter the second URL:")

    # Dropdown menu for type of conversation memory
    conversation_memory = st.sidebar.selectbox("Select conversation memory", ["buffer of 5 questions", "conversation summary", "buffer of 5,000 tokens"])

    # Sidebar for LLM selection
    llm_option = st.sidebar.selectbox("Select LLM", ["OpenAI", "Claude", "Cohere"])
    if llm_option == "OpenAI":
        model_option = st.sidebar.radio("Model selection", ["3.5-turbo", "4o-mini"])

    # Fetching content from URLs
    url1_content = read_url_content(url1) if url1 else ""
    url2_content = read_url_content(url2) if url2 else ""

    # Display an initial assistant message when the app is loaded
    with st.chat_message("assistant"):
        st.write("Hello")

    # Check if 'messages' exists in the session state; if not, initialize it
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "buffer_5_questions" not in st.session_state:
        st.session_state.buffer_5_questions = []   

    # Implement conversation memory management
    if conversation_memory == "buffer of 5 questions":
        # Keep system messages and the last 5 user-assistant message pairs
        filtered_messages = [msg for msg in st.session_state.messages if msg["role"] == "system"]
        user_assistant_messages = [msg for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]]
        st.session_state.messages = filtered_messages + user_assistant_messages[-5:]

    # After processing new input, display all chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Always display the input box for user input
    prompt = st.chat_input("Ask anything")

    # If the user has entered a prompt, process it
    if prompt:
        # Display user's message in the chat
        with st.chat_message("user"):
            st.markdown(prompt)

        # Save user's message to the session state
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Add URL content to conversation history
        url_content_message = f"URL Content from URL 1:\n{url1_content}\n\nURL Content from URL 2:\n{url2_content}"
        conversation_history = [{"role": "system", "content": """
            You are a helpful assistant. After giving any response, always ask 'Do you want more info?'. 
            If the user says 'yes', provide additional details on the previous response. If the user says 'no', ask the user what else they would like help with. 
            If the user asks a new question, answer the new question and then ask 'Do you want more info?' again.
            Provide explanations in a way that a 10-year-old can understand.
        """}]

        # Append conversation memory based on selected memory type
        conversation_history.extend(st.session_state.messages)
        conversation_history.append({"role": "system", "content": url_content_message})

        response_placeholder = st.empty()

        # Initialize assistant response
        assistant_response = ""
        if llm_option == "OpenAI":
            openai.api_key = st.secrets["API_KEY"]

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini" if model_option == "4o-mini" else "gpt-3.5-turbo",
                    messages=conversation_history
                )
                assistant_response = response["choices"][0]["message"]["content"]

            except Exception as e:
                assistant_response = f"Error: {str(e)}"

        elif llm_option == "Claude":
            try:
                # Create a client for Claude using the API key
                client = anthropic.Client(api_key=st.secrets["claude_API_KEY"])

                # Send the request with the user's document and question
                prompt = anthropic.HUMAN_PROMPT + "\n".join([msg["content"] for msg in conversation_history]) + anthropic.AI_PROMPT

                response = client.completions.create(
                    model="claude-1",  # Or use the latest available Claude model
                    prompt=prompt,
                    max_tokens_to_sample=300  # Set a token limit
                )

                # Display the response from Claude
                assistant_response = response['completion']

            except anthropic.APIError as e:
                st.error(f"Error with Claude: {str(e)}")

        # Simulate streaming by gradually revealing the response
        for i in range(0, len(assistant_response) + 1, 10):  # Adjust chunk size as needed
            response_placeholder.markdown(assistant_response[:i])
            time.sleep(0.1)

        # Display the assistant's response in the chat
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

        # Save assistant's message to the session state
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})


if __name__ == "__main__":
    run()

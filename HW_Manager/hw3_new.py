import streamlit as st
import openai
import requests
import anthropic
from bs4 import BeautifulSoup

openai.api_key = st.secrets["API_KEY"]

def read_url_content(url):
    """Fetch and parse the content from the URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()
    except requests.RequestException as e:
        st.error(f"Error reading {url}: {e}")
        return None

def run():
    # Sidebar for input of two URLs
    with st.sidebar:
        st.header("Input URLs")
        url1 = st.text_input("Enter the first URL:")
        url2 = st.text_input("Enter the second URL:")

    # Dropdown menu for conversation memory type
    Conversation_memory = st.sidebar.selectbox("Select conversation memory", ["buffer of 5 questions", "conversation summary", "buffer of 5,000 tokens"])

    # Initial setup for memory types
    if "buffer_5_questions" not in st.session_state:
        st.session_state.buffer_5_questions = []
    if "conversation_summary" not in st.session_state:
        st.session_state.conversation_summary = ""  # Keep a concise summary in session state
    if "buffer_5000_tokens" not in st.session_state:
        st.session_state.buffer_5000_tokens = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []  

    # Initialize conversation history
    conversation_history = []  

    # Sidebar for LLM selection
    llm_option = st.sidebar.selectbox("Select LLM", ["OpenAI", "Claude", "Cohere"])
    if llm_option == "OpenAI":
        model_option = st.sidebar.radio("Model Selection", ["3.5-turbo", "gpt-4o-mini"])

    # Fetching content from URLs
    url1_content = read_url_content(url1) if url1 else ""
    url2_content = read_url_content(url2) if url2 else ""

    url_content_message = f"URL Content from URL 1:\n{url1_content}\n\nURL Content from URL 2:\n{url2_content}"

    # Display an initial assistant message when the app is loaded
    with st.chat_message("assistant"):
        st.write("Hello! How can I help you today?")

    # Display the last 3 messages from chat history
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

        # Save user's message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Add system message for LLM
        conversation_history.insert(0, {
            "role": "system", 
            "content": """
                You are a helpful assistant. After giving any response, always ask 'Do you want more info?'. 
                If the user says 'yes', provide additional details on the previous response. If the user says 'no', ask the user what else they would like help with. 
                If the user asks a new question, answer the new question and then ask 'Do you want more info?' again.
                Provide explanations in a way that a 10-year-old can understand.
            """
        })
        # Add URL contents to conversation
        conversation_history.append({"role": "system", "content": url_content_message})

        # Update conversation memory based on the selected memory type
        if Conversation_memory == "buffer of 5 questions":
            if len(st.session_state.buffer_5_questions) >= 6:
                st.session_state.buffer_5_questions.pop(0)  # Remove the oldest question if the buffer is full
            st.session_state.buffer_5_questions.append(f"User: {prompt}")
            conversation_history = [{"role": "user", "content": msg} if "User:" in msg else {"role": "assistant", "content": msg} for msg in st.session_state.buffer_5_questions]

        elif Conversation_memory == "conversation summary":
            # Only append new content to the summary (to avoid repeating the whole history each time)
            new_content = f"User: {prompt}"
            summary_prompt = f"Summarize the following conversation in a concise manner:\n{url_content_message}\n{st.session_state.conversation_summary}\n{new_content}"

            try:
                # Use OpenAI to generate the summary
                summary_response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": summary_prompt}],
                    stream=False
                )
                # Extract the content and update the conversation summary
                assistant_summary = summary_response["choices"][0]["message"]["content"]

                # Update the session state's conversation summary with new summary
                st.session_state.conversation_summary = assistant_summary
                # Append the summary to the conversation history
                conversation_history = [{"role": "system", "content": assistant_summary}]
            
            except Exception as e:
                assistant_response = f"Error: {str(e)}"

        elif Conversation_memory == "buffer of 5,000 tokens":
            st.session_state.buffer_5000_tokens += f"User: {prompt} "
            if len(st.session_state.buffer_5000_tokens) > 5000:
                st.session_state.buffer_5000_tokens = st.session_state.buffer_5000_tokens[-5000:]
            conversation_history = [{"role": "system", "content": st.session_state.buffer_5000_tokens}]

        # Fetch response from selected LLM
        assistant_response = ""
        if llm_option == "OpenAI" and model_option == "gpt-4o-mini":
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=conversation_history
                )
                assistant_response = response["choices"][0]["message"]["content"]
            except Exception as e:
                assistant_response = f"Error: {str(e)}"

        elif llm_option == "OpenAI" and model_option == "3.5-turbo":
            openai.api_key = st.secrets["API_KEY"]
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=conversation_history
                )
                assistant_response = response["choices"][0]["message"]["content"]
            except Exception as e:
                assistant_response = f"Error: {str(e)}"

        elif llm_option == "Claude":
            try:
                client = anthropic.Client(api_key=st.secrets["claude_API_KEY"])
                prompt_for_claude = anthropic.HUMAN_PROMPT + "\n".join([msg["content"] for msg in conversation_history]) + anthropic.AI_PROMPT
                response = client.completions.create(
                    model="claude-1",
                    prompt=prompt_for_claude,
                    max_tokens_to_sample=300
                )
                assistant_response = response['completion']
            except anthropic.APIError as e:
                st.error(f"Error with Claude: {str(e)}")

        # After receiving the response, update the conversation memory with assistant response
        if Conversation_memory == "buffer of 5 questions":
            st.session_state.buffer_5_questions.append(f"Assistant: {assistant_response}")

        elif Conversation_memory == "conversation summary":
            # Update the summary with the assistant's response
            st.session_state.conversation_summary += f"Assistant: {assistant_response}\n"

        elif Conversation_memory == "buffer of 5,000 tokens":
            st.session_state.buffer_5000_tokens += f"Assistant: {assistant_response} "

        # Display assistant response in the chat
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

if __name__ == "__main__":
    run()

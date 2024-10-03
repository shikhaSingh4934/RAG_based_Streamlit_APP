import streamlit as st
import openai
import requests
from bs4 import BeautifulSoup
import anthropic

# Function to read content from URL
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

    # Initialize Streamlit app
    st.title("📄 New Technology for LLM")

    # Input for URL
    url = st.text_input("Enter the URL of the document")

    # Sidebar for summary type
    summary_type = st.sidebar.selectbox("Select summary type", ["Brief", "Detailed", "Custom"])

    # Dropdown menu for output language
    language = st.sidebar.selectbox("Select output language", ["English", "French", "Spanish"])

    # Sidebar for LLM selection
    llm_option = st.sidebar.selectbox("Select LLM", ["OpenAI", "Claude"])

    # Process the URL
    if url:
        content = read_url_content(url)
        if content:
            question = st.text_area("Ask a question about the document!", placeholder="Can you give me a summary?", disabled=not content)

            if question:
                # Prepare messages for LLM
                messages = [
                    {"role": "user", "content": f"Here's the document: {content} \n\n---\n\n {question} \n\nPlease respond in {language}."}
                ]  # Updated prompt to specify the response language
                
                # Use selected LLM
                if llm_option == "OpenAI":
                    openai.api_key = st.secrets["API_KEY"]
                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-4o-mini",  # Updated model name
                            messages=messages
                        )
                        st.write(response.choices[0].message['content'])
                    except Exception as e:
                        st.error(f"Error with OpenAI: {str(e)}")

                elif llm_option == "Claude":
                    try:
                        # Create a client for Claude using the API key
                        client = anthropic.Client(api_key=st.secrets["claude_API_KEY"])
                        
                        # Send the request with the user's document and question
                        prompt = anthropic.HUMAN_PROMPT + f"Here's the document: {content} \n\n---\n\n {question} \n\nPlease respond in {language}." + anthropic.AI_PROMPT
                        response = client.completions.create(
                            model="claude-1",  # Or use the latest available Claude model
                            prompt=prompt,
                            max_tokens_to_sample=300  # Set a token limit
                        )
                        
                        # Display the response from Claude
                        st.write(response['completion'])

                    except anthropic.APIError as e:
                        st.error(f"Error with Claude: {str(e)}")

                else:
                    st.error("Selected LLM is not supported.")
if __name__ == "__main__":
    run()        

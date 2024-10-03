import streamlit as st
import openai
import fitz  

def run():

    def extract_text_from_pdf(pdf_file):
        document = fitz.open(stream=pdf_file.read(), 
                            filetype="pdf")
        text = ''
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text += page.get_text()
        return text



    if 'document' not in st.session_state:
        st.session_state['document'] = None
    st.title("📄 Document Question Answering 1")
    st.write(
        "Upload a document below and ask a question about it – GPT will answer! "
        "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys)."
    )


    openai_api_key = st.text_input("OpenAI API Key", 
                                type="password")


    if openai_api_key:
        try:
            openai.api_key = openai_api_key
            openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", 
                        "content": "Test"}],
                max_tokens=5,
            )
            st.success("API key is valid! You can now upload a document and ask a question.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}", icon="🚨")
            st.stop()
    else:
        st.info("Please add your OpenAI API key to continue.", icon="🗝")
        st.stop()
    uploaded_file = st.file_uploader(
        "Upload a document (.txt or .pdf)", type=("txt", "pdf")
    )



    if uploaded_file:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'txt':
            document = uploaded_file.read().decode('utf-8')
        elif file_extension == 'pdf':
            document = extract_text_from_pdf(uploaded_file)
        else:
            st.error("Unsupported file type.")
            st.stop()
        st.session_state['document'] = document



    if not uploaded_file:
        st.session_state.pop('document', None)
    question = st.text_area(
        "Now we can ask a question about the document!",
        placeholder="Can you give me a short summary?",
        disabled='document' not in st.session_state,
    )



    if 'document' in st.session_state and question:
        document = st.session_state['document']
        messages = [
            {
                "role": "user",
                "content": f"Here's the document you will be queryed about: {document} \n\n---\n\n {question}",
            }
        ]
        try:
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  
                messages=messages,
                stream=True,
            )

            
            result = ""
            for chunk in response:
                chunk_content = chunk.choices[0].delta.get("content", "")
                result += chunk_content
                st.write(chunk_content)
        except Exception as e:
            st.error(f"Error generating a response: {str(e)}")

if __name__ == "__main__":
    run()        
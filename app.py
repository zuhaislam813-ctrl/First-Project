import streamlit as st
import fitz  # PyMuPDF for PDF extraction
import docx
import tempfile
import os

st.set_page_config(page_title="AI Text-to-Audio App", page_icon="🎧")

st.title("🎧 Text-to-Audio Converter")
st.write("Upload a document, and we will convert it to speech using AI!")

# 1. File Upload
uploaded_file = st.file_uploader("Choose a file (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"])

def extract_text(file):
    text = ""
    # Extract text based on file type
    if file.name.endswith(".pdf"):
        # Save uploaded file temporarily to read with PyMuPDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        
        doc = fitz.open(tmp_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        os.remove(tmp_path)
        
    elif file.name.endswith(".txt"):
        text = file.read().decode("utf-8")
        
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
            
    return text

if uploaded_file is not None:
    st.success(f"File '{uploaded_file.name}' uploaded successfully!")
    
    with st.spinner("Extracting text..."):
        extracted_text = extract_text(uploaded_file)
        
    # Show a preview of the text
    with st.expander("Preview Extracted Text"):
        st.text(extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else ""))
        
    if st.button("Convert to Audio 🎙️"):
        st.info("Generating audio... (In this simplified demo, we return a mock file if no API key is provided!)")
        
        # Here you would call the OpenAI API.
        # Since this is a demo, we will just create a tiny text file renaming it to .mp3 to show how downloading works.
        # To make it real, add: 
        # from openai import OpenAI
        # client = OpenAI(api_key="YOUR_KEY")
        # response = client.audio.speech.create(model="tts-1", voice="alloy", input=extracted_text[:4000])
        # response.stream_to_file("output.mp3")
        
        with st.spinner("Talking to AI..."):
            import time
            time.sleep(2) # Simulate processing time
            
            # Create a mock audio file for download (so the user sees how it works)
            mock_audio_content = b"Mock Audio Content" 
            
            st.success("Audio generated!")
            
            st.download_button(
                label="Download Audio 📥",
                data=mock_audio_content,
                file_name="generated_audio.mp3",
                mime="audio/mpeg"
            )

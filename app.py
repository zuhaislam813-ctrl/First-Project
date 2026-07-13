import streamlit as st
import fitz  # PyMuPDF for PDF extraction
import docx
import tempfile
import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

st.set_page_config(page_title="AI Text-to-Audio App", page_icon="🎧")

# Supabase Initialization
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

st.title("🎧 Text-to-Audio Converter")
st.write("Upload a document, and we will convert it to speech using AI! (Integrated with Supabase)")

# 1. File Upload
uploaded_file = st.file_uploader("Choose a file (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"])

def extract_text(file):
    text = ""
    file.seek(0)
    # Extract text based on file type
    if file.name.endswith(".pdf"):
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
    
    with st.spinner("Extracting text and uploading to Supabase..."):
        # We need to make sure we read it for extraction
        extracted_text = extract_text(uploaded_file)
        
        # We reset the pointer for supabase upload
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        
        # 1. Upload to Supabase Storage
        file_ext = uploaded_file.name.split('.')[-1]
        storage_path = f"{int(time.time())}_{uploaded_file.name}"
        
        supabase.storage.from_("raw_documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": uploaded_file.type}
        )
        
        # 2. Insert into documents table
        doc_data = {
            "filename": uploaded_file.name,
            "file_type": file_ext,
            "storage_path": storage_path,
            "extracted_text": extracted_text,
            # no user_id for now as we don't have auth setup in streamlit
        }
        
        res = supabase.table("documents").insert(doc_data).execute()
        document_id = res.data.data[0]['id'] if hasattr(res, 'data') and hasattr(res.data, 'data') else res.data[0]['id']

    # Show a preview of the text
    with st.expander("Preview Extracted Text"):
        st.text(extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else ""))
        
    if st.button("Convert to Audio 🎙️"):
        st.info("Generating audio... (In this simplified demo, we return a mock file if no API key is provided!)")
        
        with st.spinner("Talking to AI and updating Supabase..."):
            # 3. Create audio conversion record
            conv_data = {
                "document_id": document_id,
                "status": "processing"
            }
            conv_res = supabase.table("audio_conversions").insert(conv_data).execute()
            conversion_id = conv_res.data[0]['id']
            
            # Simulate processing time
            time.sleep(2) 
            
            # Create a mock audio file
            mock_audio_content = b"Mock Audio Content" 
            audio_storage_path = f"{int(time.time())}_generated_audio.mp3"
            
            # Upload generated audio to Supabase
            supabase.storage.from_("generated_audio").upload(
                path=audio_storage_path,
                file=mock_audio_content,
                file_options={"content-type": "audio/mpeg"}
            )
            
            # Update conversion record
            supabase.table("audio_conversions").update({
                "status": "completed",
                "audio_storage_path": audio_storage_path,
                "completed_at": "now()"
            }).eq("id", conversion_id).execute()
            
            st.success("Audio generated & tracked in Supabase!")
            
            st.download_button(
                label="Download Audio 📥",
                data=mock_audio_content,
                file_name="generated_audio.mp3",
                mime="audio/mpeg"
            )

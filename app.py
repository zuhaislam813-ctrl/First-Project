import streamlit as st
import fitz  # PyMuPDF for PDF extraction
import docx
import tempfile
import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from google.cloud import texttospeech

load_dotenv()

st.set_page_config(page_title="AudioSynth AI", page_icon="🎧", layout="centered")

# --- Custom CSS Injection ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #1E293B;
}

/* Background */
.stApp {
    background-color: #F8FAFC;
}

/* Hero Section */
.hero-container {
    text-align: center;
    padding: 3rem 1rem 2rem 1rem;
    margin-bottom: 2rem;
    background: linear-gradient(135deg, rgba(99,102,241,0.05) 0%, rgba(139,92,246,0.05) 100%);
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.5);
    box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);
}
.hero-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(to right, #6366F1, #8B5CF6, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: #64748B;
    font-weight: 400;
    max-width: 600px;
    margin: 0 auto;
}

/* Cards & Upload Area */
div[data-testid="stFileUploader"] {
    background-color: #FFFFFF;
    padding: 2rem;
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    border: 1px dashed #CBD5E1;
    transition: all 0.3s ease;
}
div[data-testid="stFileUploader"]:hover {
    border-color: #6366F1;
    box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.1);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(to right, #6366F1, #8B5CF6) !important;
    color: white !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39) !important;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.23) !important;
}
.stDownloadButton>button {
    background: linear-gradient(to right, #22C55E, #16A34A) !important;
    color: white !important;
    border: none !important;
    border-radius: 9999px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 14px 0 rgba(34, 197, 94, 0.39) !important;
}
.stDownloadButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(34, 197, 94, 0.23) !important;
}

/* Success/Info Alerts */
.stAlert {
    border-radius: 12px;
    border: none;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

/* Hide default hamburger menu and footer for clean SaaS look */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Supabase Initialization
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- Hero Section ---
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">AudioSynth AI</h1>
    <p class="hero-subtitle">Transform your documents into lifelike speech instantly. Upload a PDF, Word, or text file to get started.</p>
</div>
""", unsafe_allow_html=True)

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
        st.info("Generating audio with Google Cloud Text-to-Speech...")
        
        with st.spinner("Talking to AI and updating Supabase..."):
            # 3. Create audio conversion record
            conv_data = {
                "document_id": document_id,
                "status": "processing"
            }
            conv_res = supabase.table("audio_conversions").insert(conv_data).execute()
            conversion_id = conv_res.data[0]['id']
            
            # Generate audio using Google Cloud Text-to-Speech
            try:
                client = texttospeech.TextToSpeechClient(client_options={"api_key": os.environ.get("GOOGLE_API_KEY")})
                
                # Google TTS limit is 5000 bytes per request, so 4096 is safe
                text_to_speak = extracted_text[:4096] if extracted_text else "No text found."
                
                synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name="en-US-Journey-F"
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                
                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )
                audio_content = response.audio_content
            except Exception as e:
                st.error(f"Failed to generate audio with Google Cloud TTS: {e}")
                supabase.table("audio_conversions").update({
                    "status": "failed",
                    "completed_at": "now()"
                }).eq("id", conversion_id).execute()
                st.stop()
                
            audio_storage_path = f"{int(time.time())}_generated_audio.mp3"
            
            # Upload generated audio to Supabase
            supabase.storage.from_("generated_audio").upload(
                path=audio_storage_path,
                file=audio_content,
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
                data=audio_content,
                file_name="generated_audio.mp3",
                mime="audio/mpeg"
            )

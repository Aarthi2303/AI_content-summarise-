
import streamlit as st
import subprocess
import sys
import os
import io
import re
import tempfile
import base64
import time

from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def install_if_missing(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        st.info(f"⚙️ Installing missing package: `{package}`...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        except Exception as e:
            st.error(f"Failed to install {package}: {e}")

install_if_missing("SpeechRecognition", "speech_recognition")
install_if_missing("python-docx", "docx")
install_if_missing("youtube-transcript-api", "youtube_transcript_api")
install_if_missing("deep-translator", "deep_translator")
install_if_missing("streamlit-autorefresh", "streamlit_autorefresh")
install_if_missing("gTTS", "gtts")
install_if_missing("pillow", "PIL")
install_if_missing("pytesseract", "pytesseract")
install_if_missing("PyMuPDF", "fitz")
import fitz

install_if_missing("google-generativeai", "google.generativeai")
import google.generativeai as genai

# Configure Gemini if key is provided
if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("YOUR_ACTUAL"):
    genai.configure(api_key=GEMINI_API_KEY)
    HAS_GEMINI = True
else:
    HAS_GEMINI = False

import torch
from transformers import BartTokenizer, BartForConditionalGeneration
from PyPDF2 import PdfReader
import docx
import speech_recognition as sr
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from deep_translator import GoogleTranslator
from gtts import gTTS
from PIL import Image
import pytesseract
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# Tesseract Configuration (Common Path - User may need to adjust)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


st.set_page_config(page_title="Ultra Summarizer AI", layout="wide", page_icon="✨")

# Custom CSS for Premium Look
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at center, #0a0f1e 0%, #050a14 100%);
        background-attachment: fixed;
        color: #e2e8f0;
    }
    /* Animated Aurora-like subtle background effect */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(125deg, rgba(96, 165, 250, 0.03) 0%, rgba(168, 85, 247, 0.03) 50%, rgba(236, 72, 153, 0.03) 100%);
        z-index: -1;
    }
    .main-header {
        font-size: 5rem; /* Increased from 4.2rem */
        font-weight: 900;
        line-height: 1.1;
        letter-spacing: -2px;
        background: linear-gradient(135deg, #60a5fa 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        text-align: center;
    }
    .sub-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .summary-box {
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 40px;
        border-radius: 28px;
        margin-top: 30px;
        line-height: 1.9;
        font-size: 1.35rem; /* Clearly increased for better legibility */
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    .topic-header {
        color: #60a5fa;
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 2rem;
        border-bottom: 2px solid rgba(96, 165, 250, 0.2);
        padding-bottom: 8px;
    }
    .bullet-point {
        margin-left: 20px;
        margin-bottom: 12px;
        position: relative;
    }
    .example-box {
        background: rgba(96, 165, 250, 0.05);
        border-left: 4px solid #60a5fa;
        padding: 15px 20px;
        margin: 15px 0;
        border-radius: 4px 12px 12px 4px;
        font-style: italic;
        color: #cbd5e1;
    }
    .mermaid-container {
        background: white;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
        display: flex;
        justify-content: center;
    }
    /* Hero & Card System */
    .hero-container {
        padding: 60px 0;
        text-align: center;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 30px;
        margin-bottom: 40px;
    }
    .hero-subtitle {
        font-size: 1.4rem;
        font-weight: 600;
        color: #94a3b8;
        max-width: 800px;
        margin: 0 auto 30px;
    }
    .feature-card {
        background: rgba(30, 41, 59, 0.4);
        padding: 30px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: all 0.3s ease;
        height: 100%;
        text-align: center;
        font-weight: 700;
    }
    .feature-card:hover {
        background: rgba(30, 41, 59, 0.6);
        border-color: rgba(96, 165, 250, 0.3);
        transform: translateY(-5px);
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 20px;
    }
    .feature-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #60a5fa;
        margin-bottom: 10px;
    }
    .feature-desc {
        font-size: 1rem;
        color: #94a3b8;
    }
    .stButton>button {
        border-radius: 14px;
        padding: 12px 30px;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        border: none;
        color: white;
        font-weight: 700;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .stButton>button:hover {
        transform: scale(1.05) translateY(-3px);
        box-shadow: 0 10px 20px rgba(124, 58, 237, 0.4);
    }
    
    /* Specific Styling for Download Button - High Contrast Cyan */
    .stDownloadButton>button {
        background: linear-gradient(90deg, #06b6d4, #0891b2) !important;
        color: white !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton>button:hover {
        background: linear-gradient(90deg, #22d3ee, #06b6d4) !important;
        transform: scale(1.05) translateY(-2px) !important;
        box-shadow: 0 10px 20px rgba(6, 182, 212, 0.4) !important;
    }

    /* Style the Text Area boxes professionally */
    .stTextArea textarea {
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
        font-size: 1.1rem !important;
    }
    
    /* Premium Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 15, 30, 0.95) 0%, rgba(5, 10, 20, 0.95) 100%) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* High-Contrast Modern Sidebar Tabs - Uniform Size */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 10px !important;
        padding: 10px 5px !important;
        display: flex !important;
        flex-direction: column !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 0 20px !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 55px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        transition: all 0.25s ease !important;
        cursor: pointer !important;
    }
    
    /* High-Contrast Sidebar Labels - Force Visibility */
    [data-testid="stSidebar"] div[role="radiogroup"] [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-size: 1.35rem !important; /* Increased from 1.15rem */
        font-weight: 700 !important;
        margin: 0 !important;
        padding-left: 10px !important;
        opacity: 1 !important;
    }

    /* Selected State: Professional High-Contrast Sapphire */
    [data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
        border-color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important;
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5) !important;
    }

    /* Individual Module Colors on Hover */
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(59, 130, 246, 0.25) !important;
        border-color: #60a5fa !important;
        transform: translateX(4px);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover [data-testid="stMarkdownContainer"] p {
        color: #60a5fa !important;
    }

    /* Hide default radio elements */
    [data-testid="stSidebar"] div[role="radiogroup"] input { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none !important; }

    /* Professional Sidebar Headings */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        margin-bottom: 1.5rem !important;
        text-align: center !important;
    }

    .slide-container {
        animation: fadeIn 0.8s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* High-Contrast Labels for Input Fields - Increased Size */
    [data-testid="stWidgetLabel"] {
        color: #fbbf24 !important;
        font-size: 1.7rem !important; /* Significantly increased from 1.25rem */
        font-weight: 800 !important;
        text-shadow: 0 0 15px rgba(251, 191, 36, 0.2) !important;
        margin-bottom: 12px !important;
        letter-spacing: 0.5px !important;
    }

    /* Professional File Uploader Styling */
    [data-testid="stFileUploader"] {
        background-color: rgba(30, 41, 59, 0.5) !important; /* Deep charcoal/blue */
        border: 2px dashed rgba(96, 165, 250, 0.3) !important;
        border-radius: 15px !important;
        padding: 20px !important;
    }

    /* Style the 'Browse files' button specifically */
    [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; /* Emerald Gradient */
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }

    /* File Drop Zone Text Visibility */
    [data-testid="stFileUploaderDropzone"] div {
        color: #cbd5e1 !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    /* YouTube URL & Text Input Fix - Removing the white background */
    .stTextInput input {
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: #ffffff !important;
        border: 1px solid rgba(96, 165, 250, 0.4) !important;
        border-radius: 12px !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important; /* Increased font weight */
        padding: 15px !important;
    }
    
    /* Global Placeholder Styling */
    .stTextInput input::placeholder {
        color: white !important; 
        font-weight: 600 !important; 
        opacity: 0.8 !important;
    }
    
    /* For Text Area Placeholders as well */
    .stTextArea textarea::placeholder {
        color: white !important;
        font-weight: 600 !important;
        opacity: 0.8 !important;
    }

    /* YouTube Instructions Specific Styling */
    .yt-instruction {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: white !important;
        line-height: 2.2 !important;
        background: rgba(30, 41, 59, 0.4);
        padding: 25px;
        border-radius: 25px;
        border-left: 5px solid #fbbf24;
    }

    /* Target the Expander Bar (Header) */
    [data-testid="stExpander"] summary {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        font-weight: 900 !important;
        font-size: 1.3rem !important;
        transition: all 0.3s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    [data-testid="stExpander"] summary:hover {
        background: linear-gradient(90deg, #2563eb 0%, #60a5fa 100%) !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)




# 2. Cache Model Loading

@st.cache_resource
def load_model():
    # Switching to bart-large-cnn for significantly better quality while remaining local
    model_name = "facebook/bart-large-cnn"
    tokenizer = BartTokenizer.from_pretrained(model_name)
    model = BartForConditionalGeneration.from_pretrained(model_name)
    
    # Speed Optimization: Move to GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    
    # Use half precision if on GPU for double speed
    if device == "cuda":
        model = model.half()
        
    return tokenizer, model, device

with st.spinner("🚀 Waking up Local AI... (High-Speed Mode)"):
    tokenizer, model, device = load_model()


# 3. Core Text Processing Functions


def clean_input_text(text):
    """Deep clean input text while preserving mathematical symbols and table-like structures."""
    # Preserve key mathematical and structural symbols instead of stripping everything non-ASCII
    # We allow basic ASCII + common math symbols
    text = re.sub(r'\.{3,}', '', text)
    text = re.sub(r'\bPage\s+\d+\b', '', text, flags=re.IGNORECASE)
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        s = line.strip()
        if not s:
            continue
            
        # Refined TOC filter: exclude lines that look like "Chapter 1 ... 12"
        if re.search(r'[A-Za-z\s]{3,}\s*\.*\s*\d+$', s) and len(s) < 80:
            if not any(stop in s.lower() for stop in ['formula', 'equation', 'theory', 'model']):
                continue
                
        cleaned_lines.append(s)
        
    # Smart paragraph merging: join lines that don't end in punctuation
    merged = []
    current_para = []
    for line in cleaned_lines:
        current_para.append(line)
        # If line ends in sentence-ending punctuation, or looks like a heading (short, no punctuation)
        if line.endswith(('.', ':', '!', '?')) or len(line.split()) < 5:
            merged.append(" ".join(current_para))
            current_para = []
            
    if current_para:
        merged.append(" ".join(current_para))
        
    return " \n".join(merged)

def get_base64_image(file_path):
    """Convert local image to base64 for HTML embedding."""
    try:
        if not os.path.exists(file_path):
            return ""
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    except Exception as e:
        return ""

def chunk_text(text, max_tokens=800):
    """Split text into chunks. Model limit is 1024."""
    tokens = tokenizer.encode(text, add_special_tokens=False)
    for i in range(0, len(tokens), max_tokens):
        yield tokenizer.decode(tokens[i : i + max_tokens], skip_special_tokens=True)


def chunk_text_with_headings(text, max_tokens=850):
    """Chunk text while associating each chunk with its nearest structural heading."""
    lines = text.split('\n')
    chunks = []
    
    current_heading = "Initial Overview"
    current_chunk_text = []
    current_tokens = 0
    
    for line in lines:
        s = line.strip()
        if not s: continue
        
        # Heading Detection Logic
        is_new_heading = False
        words = s.split()
        if 2 <= len(s) <= 80 and words:
            # Not a full sentence and starts with Capital/Number
            if not s.endswith(('.', ',', ';', '?', '!')) and re.match(r'^[A-Z0-9]', s):
                uppercase_ratio = sum(1 for w in words if w[0].isupper()) / len(words)
                if uppercase_ratio >= 0.7 or len(words) <= 4:
                    h_clean = re.sub(r'^[\d\.\s]+', '', s).strip().title()
                    if len(h_clean) >= 4 and h_clean.lower() not in ['table of contents', 'contents', 'page']:
                        # If we have text in current chunk and a new heading appears, close the previous chunk
                        if current_chunk_text and current_tokens > 200:
                            chunks.append((current_heading, " \n".join(current_chunk_text)))
                            current_chunk_text = []
                            current_tokens = 0
                        current_heading = h_clean
                        is_new_heading = True

        approx_tokens = len(s.split())
        
        # If chunk gets too big, split it
        if current_tokens + approx_tokens > max_tokens:
            chunks.append((current_heading, " \n".join(current_chunk_text)))
            current_chunk_text = [s]
            current_tokens = approx_tokens
        else:
            current_chunk_text.append(s)
            current_tokens += approx_tokens

    if current_chunk_text:
        chunks.append((current_heading, " \n".join(current_chunk_text)))
        
    # Deduplicate "Executive Summary" if it appears too much
    seen_headings = set()
    final_chunks = []
    for h, t in chunks:
        if h == "Executive Summary" and h in seen_headings:
            h = "General Context"
        final_chunks.append((h, t))
        seen_headings.add(h)
            
    return final_chunks

def summarize_text(text, target_detail="High"):
    """Generate a high-quality AI report using either Gemini (Cloud) or BART (Local)."""
    if not text or len(text.strip()) < 30:
        return "The content provided is insufficient for analysis."


    # 1. Use Gemini if Internal API Key is configured
    if HAS_GEMINI:
        # User defined model list - using names verified in model_list.txt
        models_to_try = [
            "gemini-2.0-flash", 
            "gemini-1.5-flash", 
            "gemini-pro", 
            "gemini-2.0-flash-lite",
            "gemini-flash-latest"
        ]
        
        last_error = ""
        for model_name in models_to_try:
            try:
                # Some environments require 'models/' prefix, some don't. We'll try the name directly.
                model_gemini = genai.GenerativeModel(model_name)
                
                depth_instruction = ""
                if target_detail == "Low":
                    depth_instruction = "Provide a very CONCISE and BRIEF summary focusing only on the absolute essentials. Use fewer bullet points."
                elif target_detail == "High":
                    depth_instruction = "Provide a COMPREHENSIVE and DETAILED analysis. Elaborate on key concepts and structure it for easy reading."
                else: # "Expert"
                    depth_instruction = "Provide an EXHAUSTIVE, TECHNICAL, and IN-DEPTH intelligence report. Analyze nuances, implications, and provide a master-level breakdown of all findings."

                prompt = f"""
                You are an expert technical analyst. I want you to provide a highly professional, clear, and structured summary of the following text.
                Specific Requirement: {depth_instruction}

                Please use the following structure:
                1. # 📄 [Catchy, Relevant Title]
                2. ### 📝 Executive Overview
                   [A high-level summary of the document]
                3. ### 💎 Strategic Highlights
                   [Key takeaways with bolded concepts]
                4. ### 🔍 Professional Analysis
                   [Detailed breakdown of main themes/findings. Use subheadings if depth is 'Detailed' or 'Expert'.]
                5. ### 🏁 Actionable Conclusions
                
                Text to summarize:
                {text[:30000]}
                """
                response = model_gemini.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = str(e)
                # If this model fails or quota is hit, continue to the next one
                continue
                
        st.warning(f"⚠️ Gemini API issue: {last_error if last_error else 'All models failed'}. Falling back to Local AI.")

    # 2. Local BART-Large Mode (Fallback or Default)
    # Title Extraction
    raw_lines = text.strip().split('\n')
    extracted_title = "Technical Document Analysis"
    for line in raw_lines[:3]:
        if 3 < len(line.strip()) < 80:
            extracted_title = line.strip().strip('#').title()
            break

    cleaned_input = clean_input_text(text)
    heading_chunks = chunk_text_with_headings(cleaned_input)
    
    all_summary_blocks = []
    seen_sentences = set()
    
    progress_bar = st.progress(0, text="🧠 Analyzing with Local BART-Large...")
    
    with torch.inference_mode():
        for i, (heading, chunk) in enumerate(heading_chunks):
            progress_bar.progress((i + 1) / len(heading_chunks), text=f"Analyzing: {heading}")
            
            inputs = tokenizer.encode(chunk, return_tensors="pt", max_length=1024, truncation=True).to(device)
            input_len = len(inputs[0])
            if input_len < 15: continue
            
            # Dynamic length settings based on user preference
            if target_detail == "Low":
                max_l, min_l = 150, 40
            elif target_detail == "High":
                max_l, min_l = 450, 80
            else: # "Expert"
                max_l, min_l = 850, 150

            summary_ids = model.generate(
                inputs,
                max_length=max_l,
                min_length=min_l,
                length_penalty=2.0,
                num_beams=4,
                no_repeat_ngram_size=3,
                early_stopping=True
            )
            
            decoded = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            all_summary_blocks.append((heading, decoded))
            
    progress_bar.empty()
    
    # Post-Processing into ChatGPT-style Format
    output = f"# 📄 {extracted_title}\n\n"
    output += "### 📝 Executive Overview\n"
    if all_summary_blocks:
        output += f"{all_summary_blocks[0][1].split('. ')[0]}.\n\n"
    
    output += "### 💎 Key Highlights\n"
    highlights = []
    for _, b in all_summary_blocks:
        sents = [s.strip() for s in b.split('. ') if len(s) > 40]
        highlights.extend(sents[:1])
    
    for h in highlights[:6]:
        # Bold key words for that ChatGPT look
        words = h.split()
        if len(words) > 5:
            words[0] = f"**{words[0]}"
            words[1] = f"{words[1]}**"
        output += f"- {' '.join(words)}.\n"
    output += "\n"

    output += "### 🔍 In-Depth Summary\n"
    for heading, block in all_summary_blocks:
        if len(block) < 50: continue
        output += f"#### 📌 {heading}\n"
        output += f"{block}\n\n"

    output += "### 🏁 Conclusion\n"
    if all_summary_blocks:
        output += f"Ultimately, the analysis indicates that {all_summary_blocks[-1][1].split('. ')[-1].lower()}."
    else:
        output += "The document provides a comprehensive overview of the subject matter."

    return output




def text_to_speech(text):
    """Convert text to speech and return bytes."""
    try:
        # Remove markdown formatting for clear speech
        clean_text = re.sub(r'[*#_~🌟🔹✅]', '', text)
        clean_text = re.sub(r'\d+\.', '', clean_text)
        clean_text = clean_text.replace("##", "").strip()
        
        # Truncate to avoid gTTS limits (approx 5000 chars)
        if len(clean_text) > 4500:
            clean_text = clean_text[:4500] + "... [Text truncated for voice output]"

        tts = gTTS(text=clean_text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        print(f"gTTS Error: {e}")
        return None


# 4. Content Extraction Helpers

def extract_pdf_images(file_bytes):
    images = []
    seen_xrefs = set()
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                
                # Prevent extracting the exact same structural logo from every single page!
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                
                base_image = doc.extract_image(xref)
                
                # Filter out small images like icons or lines
                if base_image.get("width", 0) < 100 or base_image.get("height", 0) < 100:
                    continue
                    
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                images.append(image)
    except Exception as e:
        pass
    return images



def extract_pdf(file):
    try:
        reader = PdfReader(file)
        return " ".join([page.extract_text() or "" for page in reader.pages]).strip()
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_docx(file):
    try:
        doc = docx.Document(io.BytesIO(file.read()))
        return " ".join([para.text for para in doc.paragraphs]).strip()
    except Exception as e:
        return f"Error reading DOCX: {e}"

# Video and Audio processing functions removed as per user request

# 5. Shared Summary View

def show_summary_view(text, key, extracted_images=None):
    st.divider()
    st.markdown("### 🛠️ Summarization Settings")
    col1, col2 = st.columns([1.5, 1])
    with col1:
        detail = st.select_slider("Explanation Depth", options=["Short", "Detailed", "Expert"], value="Detailed", key=f"depth_{key}")
    
    gen_btn = st.button("🚀 Generate Detailed Summary", key=f"btn_{key}")
    
    if gen_btn:
        if not text or len(str(text).strip()) < 10:
            st.warning("⚠️ Please provide content/input before generating a summary.")
        else:
            with st.spinner("🧠 AI is thinking deeply..."):
                summary_text = summarize_text(text, target_detail=DETAIL_MAP[detail])
                st.session_state[f"result_{key}"] = summary_text
                st.session_state[f"images_{key}"] = extracted_images

    if f"result_{key}" in st.session_state:
        res = st.session_state[f"result_{key}"]
        # ... (rest of function)
        st.markdown(f"<div class='summary-box'>{res}</div>", unsafe_allow_html=True)
        
        # Display Extracted Images
        imgs = st.session_state.get(f"images_{key}", None)
        if imgs and len(imgs) > 0:
            st.markdown("### 🖼️ Extracted Visuals & Examples")
            st.write("The AI automatically detected and extracted the following visuals from your input:")
            cols = st.columns(len(imgs))
            for k, col in enumerate(cols):
                with col:
                    st.image(imgs[k], use_container_width=True, caption=f"Extracted Image {k+1}")

        
        st.divider()
        st.markdown("### 🎙️ Voice & Download")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔊 Hear Summary (Voice)", key=f"vbtn_{key}"):
                with st.spinner("Generating voice..."):
                    audio_fp = text_to_speech(res)
                    if audio_fp:
                        st.audio(audio_fp, format="audio/mp3")
                    else:
                        st.error("🚫 Voice generation failed. This usually happens due to a network issue with Google TTS servers. Please check your internet connection and try again.")
        with c2:
            st.download_button("📥 Download Detailed Report", data=res, file_name="AI_Summary_Report.txt", key=f"dl_{key}")

DETAIL_MAP = {"Short": "Low", "Detailed": "High", "Expert": "Extreme"}

# 6. Sidebar & Routing

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4712/4712027.png", width=120)
st.sidebar.title("Navigator")



page = st.sidebar.radio("CORE MODULES", [
    "🏠 HOME", "💬Direct Text", "📄 File Analysis", "📺 YouTube Link", "🖼️ Image OCR", "🌍 Translator"
])


if page == "🏠 HOME":
    # Trigger 5-second auto-refresh for slideshow
    st_autorefresh(interval=5000, key="about_slideshow")

    # 1. Main Titles & Hero Section
    st.markdown("<h2 class='sub-header'>Extract and Summarizing</h2>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-header'>AI-Powered Multi-Modal Content Summarizer</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; margin-bottom: 3rem;'>
        <p style='font-size: 1.3rem; color: #94a3b8; max-width: 900px; margin: 0 auto;'> 
        Transform complex documents, videos, and images into clear and structured insights using Artificial Intelligence.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Hero Image Display
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.image("ai_summarizer_hero_v2_1772970721422.png", use_container_width=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 2. Features Grid Section
    st.markdown("<h3 style='text-align: center; font-size: 2.2rem; font-weight: 800; margin-bottom: 3rem;'>System Modules</h3>", unsafe_allow_html=True)
    
    row1_c1, row1_c2, row1_c3 = st.columns(3)
    with row1_c1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div class="feature-title">Direct Text Summarization</div>
            <div class="feature-desc">Paste raw notes, articles, or research papers directly to get a professional technical overview.</div>
        </div>
        """, unsafe_allow_html=True)
    with row1_c2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <div class="feature-title">File Analysis</div>
            <div class="feature-desc">Structural analysis of PDF, DOCX, and TXT files with support for image extraction from graphics.</div>
        </div>
        """, unsafe_allow_html=True)
    with row1_c3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <div class="feature-title">System Intelligence</div>
            <div class="feature-desc">Utilizes advanced transformer models to ensure high-accuracy content synthesis and report generation.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    row2_c1, row2_c2, row2_c3 = st.columns(3)
    with row2_c1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📺</div>
            <div class="feature-title">YouTube Transcript Analysis</div>
            <div class="feature-desc">Extract knowledge from any YouTube video by automatically analyzing its transcript.</div>
        </div>
        """, unsafe_allow_html=True)
    with row2_c2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🖼️</div>
            <div class="feature-title">Image OCR</div>
            <div class="feature-desc">Advanced Optical Character Recognition to extract and summarize text from images and screenshots.</div>
        </div>
        """, unsafe_allow_html=True)
    with row2_c3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🌍</div>
            <div class="feature-title">Multi-Language Translator</div>
            <div class="feature-desc">Translate your technical summaries into 10+ global languages, including AI-powered Thanglish.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 3. About Section (Professional Slide Presentation & Auto-Rotation)
    if 'about_slide' not in st.session_state:
        st.session_state.about_slide = 0
    if 'last_slide_time' not in st.session_state:
        st.session_state.last_slide_time = time.time()

    slides = [
        {
            "title": "System Overview",
            "content": "Ultra Summarizer AI is a professional intelligence platform engineered to extract, analyze, and condense information from a heterogeneous ecosystem of data sources. By unifying PDF, DOCX, and Visual data into a single coherent analytical stream, the system empowers users to synthesize critical insights from massive datasets in seconds.",
            "img": "ai_summarizer_hero_v2_1772970721422.png",
            "tag": "Enterprise Intelligence"
        },
        {
            "title": "BART Transformer Architecture",
            "content": "Powering our core is the <b>BART (Bidirectional and Auto-Regressive Transformers)</b> architecture. This state-of-the-art neural engine processes natural language with superior contextual awareness, generating summaries that aren't just shortened text, but structured intelligence reports. Integrated OCR modules ensure seamless conversion across all media types.",
            "img": "ai_transformer_network_1772972028590.png",
            "tag": "Transformer Technology"
        },
        {
            "title": "Core Strategic Objectives",
            "content": "Our primary mission is the elimination of information noise. Ultra Summarizer AI optimizes organizational productivity by distilling complex, high-entropy content into actionable intelligence. By reducing document processing time by up to 90%, the system allows professionals to focus on decision-making rather than data manual reading.",
            "img": "ai_productivity_clock_1772972043840.png",
            "tag": "Strategic Value"
        }
    ]

    # Auto-Rotation Logic (5 Seconds)
    if time.time() - st.session_state.last_slide_time > 5:
        st.session_state.about_slide = (st.session_state.about_slide + 1) % len(slides)
        st.session_state.last_slide_time = time.time()
        st.rerun()

    current_idx = st.session_state.about_slide
    current_slide = slides[current_idx]

    # Pre-encode image for reliable display
    b64_img = get_base64_image(current_slide['img'])

    # Render Active Slide with Enhanced Split Design
    st.markdown(f"""
    <div class="slide-container" style='background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(20px); padding: 0; border-radius: 30px; border: 1px solid rgba(255, 255, 255, 0.08); margin-top: 40px; min-height: 450px; overflow: hidden; box-shadow: 0 40px 100px rgba(0,0,0,0.5);'>
        <div style='display: flex; flex-wrap: wrap; height: 100%;'>
            <!-- Content Panel -->
            <div style='flex: 1.2; padding: 50px; min-width: 350px;'>
                <div style='display: inline-block; background: rgba(96, 165, 250, 0.1); color: #60a5fa; padding: 6px 16px; border-radius: 50px; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; margin-bottom: 20px; letter-spacing: 1px;'>
                    {current_slide['tag']}
                </div>
                <h3 style='font-size: 2.2rem; font-weight: 800; color: #ffffff; margin-bottom: 25px; line-height: 1.2;'>{current_slide['title']}</h3>
                <p style='font-size: 1.15rem; color: #94a3b8; line-height: 1.9; font-weight: 600; margin-bottom: 0;'>
                    {current_slide['content']}
                </p>
            </div>
            <!-- Image Panel -->
            <div style='flex: 0.8; position: relative; min-width: 300px; background: rgba(0,0,0,0.2);'>
                <img src='{b64_img}' style='width: 100%; height: 100%; object-fit: cover; opacity: 0.8;'>
                <div style='position: absolute; bottom: 30px; right: 30px; background: rgba(0,0,0,0.6); backdrop-filter: blur(10px); color: #ffffff; padding: 8px 15px; border-radius: 12px; font-weight: 700; border: 1px solid rgba(255,255,255,0.1);'>
                    Slide {current_idx + 1} / {len(slides)}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Professional Navigation Controls
    col_nav_1, col_nav_2, col_nav_3 = st.columns([1, 4, 1])
    with col_nav_1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.about_slide = (st.session_state.about_slide - 1) % len(slides)
            st.session_state.last_slide_time = time.time()
            st.rerun()
    with col_nav_3:
        if st.button("Next ➡️", use_container_width=True):
            st.session_state.about_slide = (st.session_state.about_slide + 1) % len(slides)
            st.session_state.last_slide_time = time.time()
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("💡 Pro Tip: Select an input module from the sidebar to begin processing your content.")

elif page == "💬Direct Text":
    st.subheader("💬 Manual Text Analysis")
    st.write("Paste your raw text (articles, emails, notes) below for an expert intelligence breakdown.")
    raw_text = st.text_area("Input Content", height=400, placeholder="Paste your text here...")
    # Button is now always showing inside show_summary_view
    show_summary_view(raw_text, "manual")

elif page == "📄 File Analysis":
    st.subheader("📄 Upload Document (PDF, DOCX, TXT)")
    uploaded_file = st.file_uploader("Drop your file here", type=["pdf", "docx", "txt"])
    content = ""
    extracted_images = []
    
    if uploaded_file:
        with st.spinner("Analyzing document structure..."):
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            
            if uploaded_file.name.endswith(".pdf"):
                content = extract_pdf(uploaded_file)
                try:
                    with st.spinner("Extracting hidden graphics/images..."):
                        extracted_images = extract_pdf_images(file_bytes)
                except: pass
            elif uploaded_file.name.endswith(".docx"): 
                content = extract_docx(uploaded_file)
            else: 
                content = file_bytes.decode("utf-8")
        st.success(f"Successfully read {len(content.split())} words.")
        with st.expander("📝 Preview Extracted Content"):
            st.text_area("File Text (Review Original)", content, height=300, key="file_preview")

    show_summary_view(content, "file", extracted_images)



elif page == "📺 YouTube Link":
    st.subheader("📺 YouTube Intelligence")
    
    # Simple Instructions for the user
    with st.expander("📖 How to Use", expanded=True):
        st.markdown("""
        <div class="yt-instruction">
        1. <b>Find a Video:</b> Copy the link of a YouTube video (must have <b>Captions/CC</b> enabled).<br>
        2. <b>Paste URL:</b> Paste the link into the input box below.<br>
        3. <b>Extract:</b> Click 'Extract Knowledge' to load the transcript.<br>
        4. <b>Analyze:</b> Choose your explanation depth and generate the summary!
        </div>
        """, unsafe_allow_html=True)
        
    yt_url = st.text_input("Paste YouTube Video URL", placeholder=" Enter the URL of the video here eg: https://www.youtube.com/watch?v=...")
    yt_btn = st.button("🔗 Extract Knowledge")
    
    if yt_btn:
        if yt_url:
            with st.spinner("Fetching YouTube transcripts..."):
                video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", yt_url)
                if video_id_match:
                    try:
                        api = YouTubeTranscriptApi()
                        try:
                            ts = api.fetch(video_id_match.group(1), languages=['en'])
                        except Exception:
                            ts = api.fetch(video_id_match.group(1))
                        
                        yt_txt = " ".join([x.text for x in ts])
                        st.session_state["yt_txt"] = yt_txt
                        st.success("Transcript loaded successfully!")
                    except Exception as e:
                        st.error(f"Could not load transcript: {e}. (Ensure captions are enabled on the video)")
                else: st.error("Invalid YouTube URL.")
        else:
            st.warning("⚠️ Please paste a YouTube URL first.")

    if "yt_txt" in st.session_state:
        st.text_area("Video Transcript", st.session_state["yt_txt"], height=400)
        show_summary_view(st.session_state["yt_txt"], "youtube")

elif page == "🖼️ Image OCR":
    st.subheader("🖼️ Image Intelligence (OCR)")
    img_up = st.file_uploader("Upload Screenshot or Document Photo", type=["png", "jpg", "jpeg"])
    ocr_btn = st.button("👁️ Scan & Summarize")
    
    if img_up:
        img_obj = Image.open(img_up)
        st.image(img_obj, caption="Uploaded Image", use_container_width=True)

    if ocr_btn:
        if img_up:
            with st.spinner("Extracting text from pixels..."):
                try:
                    img_obj = Image.open(img_up)
                    ocr_text = pytesseract.image_to_string(img_obj)
                    if ocr_text.strip():
                        st.session_state["ocr_res"] = ocr_text
                        st.success("Text detected!")
                    else: st.warning("No text found in image.")
                except Exception as e:
                    st.error("Tesseract Error. Ensure Tesseract OCR is installed on the system.")
        else:
            st.warning("⚠️ Please upload an image first.")

    if "ocr_res" in st.session_state:
        st.text_area("Detected Text", st.session_state["ocr_res"], height=400)
        show_summary_view(st.session_state["ocr_res"], "image")

elif page == "🌍 Translator":
    st.subheader("🌍 Multi-Language AI Translator")
    st.write("Convert technical summaries or any text into your preferred global language.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        input_t = st.text_area("Source Text", height=250, placeholder="Paste text here...")
    with col2:
        langs = {"English": "en", "Hindi": "hi", "Tamil": "ta", "Thanglish": "thanglish", "Spanish": "es", "French": "fr", "Malayalam": "ml", "Telugu": "te", "German": "de", "Japanese": "ja"}
        dest = st.selectbox("Select Target Language", list(langs.keys()))
        translate_btn = st.button("🌍 Translate Content")

    if translate_btn and input_t:
        with st.spinner(f"🔄 AI is translating to {dest}..."):
            res_t = ""
            try:
                # 1. Try Gemini first (Best for Thanglish and Context)
                if HAS_GEMINI:
                    model_gemini = genai.GenerativeModel("gemini-2.5-flash")
                    prompt = f"Translate the following text into {dest}. "
                    if dest == "Thanglish":
                        prompt = "Translate the following text into Thanglish (Tamil language written using English/Latin alphabet). "
                    
                    prompt += f"\n\nText:\n{input_t[:15000]}"
                    response = model_gemini.generate_content(prompt)
                    res_t = response.text
                
                # 2. Fallback to Google Translator if Gemini failed or is unavailable
                if not res_t:
                    if dest == "Thanglish":
                        st.warning("⚠️ Thanglish requires a Gemini API Key. Falling back to Standard Tamil.")
                        translator = GoogleTranslator(source='auto', target='ta')
                    else:
                        translator = GoogleTranslator(source='auto', target=langs[dest])
                    
                    lines = input_t.split('\n')
                    chunks = []
                    current_chunk = ""
                    for line in lines:
                        if len(current_chunk) + len(line) + 1 < 4500:
                            current_chunk += line + "\n"
                        else:
                            chunks.append(current_chunk.strip())
                            current_chunk = line + "\n"
                    if current_chunk: chunks.append(current_chunk.strip())
                    
                    translated_chunks = [translator.translate(c) for c in chunks if c]
                    res_t = "\n\n".join(translated_chunks)

                st.success(f"Translation Successful!")
                st.markdown(f"### 🌐 Translated Output ({dest})")
                st.markdown(f"<div class='summary-box'>{res_t}</div>", unsafe_allow_html=True)
                st.download_button("📥 Download Translation", data=res_t, file_name=f"Translated_{dest}.txt")
            except Exception as e:
                st.error(f"Translation Error: {e}")
    elif translate_btn:
        st.warning("Please provide some text to translate.")

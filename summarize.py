#PDF Summarization Using BART In Streamlit 
#%%writefile app.py
import streamlit as st
from PyPDF2 import PdfReader
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

# Set page config (must be the first Streamlit command)
st.set_page_config(page_title="PDF Summarizer", page_icon="📄", layout="wide")

# Set up the upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load the pre-trained BART tokenizer and model
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
    return tokenizer, model

tokenizer, model = load_model()

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def summarize_text(text):
    inputs = tokenizer(text, max_length=1024, return_tensors="pt", truncation=True)
    summary_ids = model.generate(inputs["input_ids"], num_beams=4, max_length=300, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
        color: #1e1e1e;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        transition-duration: 0.4s;
        cursor: pointer;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stTextArea>div>div>textarea {
        background-color: #ffffff;
        color: #1e1e1e;
        border-radius: 10px;
        padding: 10px 20px; 
        font-size: 16px;
        border: 2px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);   
        
        
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    </style>
    """, unsafe_allow_html=True)

# App title with custom styling
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📄 PDF Summarizer Pro</h1>", unsafe_allow_html=True)

st.markdown("---")

# Two-column layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        if st.button("🚀 Summarize PDF"):
            with st.spinner("Extracting text from PDF..."):
                text = extract_text_from_pdf(uploaded_file)
            
            with st.spinner("Generating summary..."):
                summary = summarize_text(text)
            
            st.success("Summary generated successfully!")
            st.subheader("📝 Summary:")
            st.markdown(f"<div style='background-color: #ffffff; padding: 20px; border-radius: 5px;'>{summary}</div>", unsafe_allow_html=True)

with col2:
    st.subheader("✍️ Or enter text to summarize")
    text_input = st.text_area("Enter your text here:", height=200)

    if st.button("🚀 Summarize Text"):
        if text_input:
            with st.spinner("Generating summary..."):
                summary = summarize_text(text_input)
            st.success("Summary generated successfully!")
            st.subheader("📝 Summary:")
            st.markdown(f"<div style='background-color: #ffffff; padding: 20px; border-radius: 5px;'>{summary}</div>", unsafe_allow_html=True)
        else:
            st.warning("Please enter some text to summarize.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #7f8c8d;'>Powered by AI - Summarize your documents with ease!</p>", unsafe_allow_html=True)
        
#!wget -q -O - https://loca.lt/mytunnelpassword

#!streamlit run app.py & npx localtunnel --port 8501        
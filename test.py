import streamlit as st
import pdfplumber
import docx
import openai

# --- Initialize OpenAI client for v1+ ---
from openai import OpenAI

# --- Session state init ---
if "page" not in st.session_state:
    st.session_state.page = "main"
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "reveal" not in st.session_state:
    st.session_state.reveal = False
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None
if "uploaded_text" not in st.session_state:
    st.session_state.uploaded_text = ""
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""



# --- Sidebar API key (persisted) ---
st.sidebar.title("🔐 API Setup")
st.session_state.openai_api_key = st.sidebar.text_input(
    "Enter your OpenAI API Key", type="password", value=st.session_state.openai_api_key
)

client = OpenAI(api_key=st.session_state.openai_api_key)

# --- File extractors ---
def extract_pdf_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text

def extract_docx_text(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_txt_text(file):
    return file.read().decode("utf-8")

# --- Main Interface ---
st.title("📚 Smart Study Helper (GPT-powered)")
uploaded_file = st.file_uploader("📤 Upload your notes or book", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1]
    st.session_state.uploaded_filename = uploaded_file.name

    if file_type == "pdf":
        text = extract_pdf_text(uploaded_file)
    elif file_type == "docx":
        text = extract_docx_text(uploaded_file)
    elif file_type == "txt":
        text = extract_txt_text(uploaded_file)
    else:
        st.error("Unsupported file type.")
        text = ""

    st.session_state.uploaded_text = text

# --- Show extracted text if available ---
if st.session_state.uploaded_text:
    st.subheader("📄 Extracted Text")
    st.text_area("Text from file:", value=st.session_state.uploaded_text, height=250)
    text = st.session_state.uploaded_text

else:
    text = ""
    st.info("Upload a file and enter your API key to enable GPT features.")
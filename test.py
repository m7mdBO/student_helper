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

# --- Flashcard Viewer Page ---
if st.session_state.page == "flashcards":
    st.title("🧠 Flashcard Viewer")

    st.markdown("### ")
    if st.button("🏠 Back to Home"):
        st.session_state.page = "main"
        st.session_state.flashcard_index = 0
        st.session_state.reveal = False
        st.rerun()

    flashcards = st.session_state.flashcards
    index = st.session_state.flashcard_index
    reveal = st.session_state.reveal

    if not flashcards:
        st.warning("⚠️ No flashcards available.")
        st.stop()

    question, answer = flashcards[index]

    # --- Styled card container ---
    with st.container():
        st.markdown(f"""
        <div style="background-color:#ffffff; padding: 25px 20px; border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-top: 20px;
                    border-left: 6px solid #4a90e2;">
            <h5 style='margin-bottom: 10px; color:#333;'>🧠 Flashcard {index + 1} of {len(flashcards)}</h5>
            <p style='font-size: 18px; color:#222;'><strong>❓ Question:</strong><br>{question}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ")

    if not reveal:
        if st.button("👀 Reveal Answer"):
            st.session_state.reveal = True
            st.rerun()
    else:
        # --- Answer styled card ---
        with st.container():
            st.markdown(f"""
            <div style="background-color:#e6f0fa; padding: 20px; border-radius: 10px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #007acc;">
                <p style='font-size: 18px; color:#003366;'><strong>✅ Answer:</strong><br>{answer}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### ")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Back to Question"):
                st.session_state.reveal = False
                st.rerun()
        with col2:
            if index + 1 < len(flashcards):
                if st.button("➡️ Next Card"):
                    st.session_state.flashcard_index += 1
                    st.session_state.reveal = False
                    st.rerun()
            else:
                st.success("🎉 You've reached the end of your flashcards.")
                if st.button("🔁 Restart"):
                    st.session_state.flashcard_index = 0
                    st.session_state.reveal = False
                    st.rerun()
    st.stop()

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

if st.session_state.openai_api_key and text:
    # --- GPT Summary ---
    st.subheader("🧠 AI Summary (GPT-3.5)")

    summary_type = st.selectbox(
        "Choose summary style:",
        ["Short", "Medium", "Long", "Bullet Points"]
    )

    if st.button("Summarize Text"):
        with st.spinner("Summarizing..."):
            try:
                if summary_type == "Short":
                    style_instruction = "Write a very concise summary in 3-5 sentences."
                elif summary_type == "Medium":
                    style_instruction = "Write a clear and balanced summary in 5-8 sentences."
                elif summary_type == "Long":
                    style_instruction = "Write a detailed summary covering all main points."
                elif summary_type == "Bullet Points":
                    style_instruction = "Summarize the content using bullet points only."

                summary_prompt = f"""{style_instruction}

Text:
{text[:2000]}
"""

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You summarize academic and lecture notes."},
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=500
                )
                summary = response.choices[0].message.content
                st.success("✅ Summary:")
                st.write(summary)

            except Exception as e:
                st.error(f"❌ Error: {e}")

    # --- GPT Flashcards ---
    st.subheader("🧠 Flashcards (Q&A with GPT-3.5)")
    if st.button("Generate Flashcards"):
        with st.spinner("Generating flashcards..."):
            try:
                flashcard_prompt = f"""
Read this text and create 5 flashcards with questions and answers.

Format:
Q1: ...
A1: ...
Q2: ...
A2: ...
(etc.)

Text:
{text[:2000]}
"""
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You generate flashcards for study."},
                        {"role": "user", "content": flashcard_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=500
                )
                flashcards_raw = response.choices[0].message.content

                def parse_flashcards(text):
                    lines = text.strip().split("\n")
                    flashcards = []
                    i = 0
                    while i < len(lines):
                        if lines[i].startswith("Q") and i + 1 < len(lines) and lines[i + 1].startswith("A"):
                            q = lines[i].split(":", 1)[-1].strip()
                            a = lines[i + 1].split(":", 1)[-1].strip()
                            flashcards.append((q, a))
                            i += 2
                        else:
                            i += 1
                    return flashcards

                st.session_state.flashcards = parse_flashcards(flashcards_raw)
                st.session_state.flashcard_index = 0
                st.session_state.reveal = False
                st.session_state.page = "flashcards"
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")
else:
    st.info("Upload a file and enter your API key to enable GPT features.")
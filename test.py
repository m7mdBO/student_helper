import streamlit as st

import pdfplumber
import docx
import openai
import os

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

# --- Unified single-file app with custom navigation and persistent state ---
import streamlit as st
import pdfplumber
import docx
import openai
import json
import os

# --- Session state init ---
def init_state():
    defaults = {
        "page": "main",
        "flashcards": [],
        "flashcard_index": 0,
        "reveal": False,
        "uploaded_filename": None,
        "uploaded_text": "",
        "openai_api_key": "",
        "quiz": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

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

# --- Sidebar API key (persisted) ---
st.sidebar.title("� API Setup")
st.session_state.openai_api_key = st.sidebar.text_input(
    "Enter your OpenAI API Key", type="password", value=st.session_state.openai_api_key
)
openai.api_key = st.session_state.openai_api_key

# --- Navigation bar (no sidebar) ---
def nav_bar():
    pass  # Navigation bar is now handled in each page as needed

# --- Main Interface ---
def main_page():
    st.title("📚 Smart Study Helper (GPT-powered)")
    uploaded_file = st.file_uploader("📤 Upload your notes or book", type=["pdf", "docx", "txt"])
    # Centered navigation buttons with equal size
    st.markdown("""
        <style>
        .centered-btn-row {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .centered-btn-row button {
            min-width: 180px !important;
            max-width: 200px !important;
            height: 48px !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    btn1, btn2, btn3 = st.columns([2,2,2], gap="large")
    with btn1:
        btn_flash = st.button("🧠 Flashcards", key="main_flash", use_container_width=True)
    with btn2:
        btn_quiz = st.button("❓ Quiz", key="main_quiz", use_container_width=True)
    with btn3:
        btn_sum = st.button("📝 Summarizer", key="main_sum", use_container_width=True)
    if btn_flash:
        st.session_state.page = "flashcards"
        st.rerun()
    if btn_quiz:
        st.session_state.page = "quiz"
        st.rerun()
    if btn_sum:
        st.session_state.page = "summarizer"
        st.rerun()
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
    if st.session_state.uploaded_text:
        st.subheader("📄 Extracted Text")
        st.text_area("Text from file:", value=st.session_state.uploaded_text, height=250)
        text = st.session_state.uploaded_text
    else:
        text = ""
    # Removed AI Summary and Flashcards generation sections from main page
    pass

# --- Flashcard Viewer Page ---
def flashcard_page():
    st.title("🧠 Flashcard Viewer")
    # Home button at top
    if st.button("🏠 Home", key="fc_home"):
        st.session_state.page = "main"
        st.session_state.flashcard_index = 0
        st.session_state.reveal = False
        st.rerun()
    # Add Generate Flashcards button (like summarizer page)
    st.subheader("Regenerate Flashcards")
    if not st.session_state.openai_api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to use the flashcard generator.")
        st.stop()
    if not st.session_state.uploaded_text:
        st.info("Please upload a file on the home page to generate flashcards.")
        st.stop()
    if st.button("Generate Flashcards", key="fc_generate"):
        with st.spinner("Generating flashcards..."):
            try:
                client = OpenAI(api_key=st.session_state.openai_api_key)
                flashcard_prompt = f"""
Read this text and create 5 flashcards with questions and answers.

Format:
Q1: ...
A1: ...
Q2: ...
A2: ...
(etc.)

Text:
{st.session_state.uploaded_text[:2000]}
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
                st.success("Flashcards generated!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    flashcards = st.session_state.flashcards
    index = st.session_state.flashcard_index
    reveal = st.session_state.reveal
    if not flashcards:
        st.warning("⚠️ No flashcards available.")
        st.stop()
    question, answer = flashcards[index]
    with st.container():
        st.markdown(f"""
        <div style=\"background-color:#ffffff; padding: 25px 20px; border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-top: 20px;
                    border-left: 6px solid #4a90e2;\">
            <h5 style='margin-bottom: 10px; color:#333;'>🧠 Flashcard {index + 1} of {len(flashcards)}</h5>
            <p style='font-size: 18px; color:#222;'><strong>❓ Question:</strong><br>{question}</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("### ")
    if reveal:
        with st.container():
            st.markdown(f"""
            <div style=\"background-color:#e6f0fa; padding: 20px; border-radius: 10px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #007acc;\">
                <p style='font-size: 18px; color:#003366;'><strong>✅ Answer:</strong><br>{answer}</p>
            </div>
            """, unsafe_allow_html=True)
    # Navigation buttons always under the answer/question
    st.markdown("### ")
    nav_cols = st.columns([1, 1, 1])
    with nav_cols[0]:
        if index > 0:
            if st.button("⬅️ Previous Card"):
                st.session_state.flashcard_index -= 1
                st.session_state.reveal = False
                st.rerun()
    with nav_cols[1]:
        if not reveal:
            if st.button("👀 Reveal Answer"):
                st.session_state.reveal = True
                st.rerun()
        else:
            if st.button("🔄 Back to Question"):
                st.session_state.reveal = False
                st.rerun()
    with nav_cols[2]:
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


# --- Quiz Page ---
def quiz_page():
    st.title("❓ Quiz")
    # Home button at top
    if st.button("🏠 Home", key="quiz_home"):
        st.session_state.page = "main"
        st.rerun()
    # Helper: get_quiz_prompt
    def get_quiz_prompt(text):
        return f"""
Read the following text and generate a 10-question multiple-choice quiz. Each question should have 4 options (A, B, C, D) and specify the correct answer as 'answer': 'A' (or B/C/D). Return as a JSON list like this:
[
  {{"question": "...", "options": ["...", "...", "...", "..."], "answer": "A"}},
  ...
]

Text:
{text[:2000]}
"""
    # Quiz generation button
    if st.button("📝 Generate Quiz", key="generate_quiz_btn"):
        if not st.session_state.openai_api_key:
            st.warning("Please enter your OpenAI API key in the sidebar to use the quiz generator.")
            st.stop()
        if not st.session_state.uploaded_text:
            st.info("Please upload a file on the home page to generate a quiz.")
            st.stop()
        with st.spinner("Generating quiz with ChatGPT..."):
            try:
                client = OpenAI(api_key=st.session_state.openai_api_key)
                prompt = get_quiz_prompt(st.session_state.uploaded_text)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1200,
                    temperature=0.7
                )
                content = response.choices[0].message.content.strip()
                start = content.find('[')
                end = content.rfind(']') + 1
                quiz_json = content[start:end]
                quiz = json.loads(quiz_json)
                st.session_state.quiz = quiz
                st.session_state.quiz_submitted = False
                st.success("Quiz generated!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate quiz: {e}")
                st.stop()
    quiz = st.session_state.get("quiz")
    if quiz:
        st.subheader("Your Multiple-Choice Quiz:")
        if "quiz_submitted" not in st.session_state:
            st.session_state.quiz_submitted = False
        user_answers = {}
        for idx, q in enumerate(quiz):
            st.markdown(f"""
                <div style='color:#1a237e; font-size:1.1rem; font-weight:600; margin-bottom:0.5rem;'>
                    Q{idx+1}. {q['question']}
                </div>
            """, unsafe_allow_html=True)
            user_answers[idx] = st.radio(
                label="",
                options=["A", "B", "C", "D"],
                format_func=lambda x: f"{x}: {q['options'][ord(x)-65]}",
                key=f"quiz_q{idx}"
            )
        if not st.session_state.quiz_submitted:
            if st.button("Submit Quiz", key="submit_quiz"):
                st.session_state.quiz_submitted = True
                st.session_state.quiz_user_answers = user_answers
                st.session_state.page = "quiz_answers"
                st.rerun()
            st.info("Select your answers and click 'Submit Quiz' to see results.")
        else:
            st.session_state.page = "quiz_answers"
            st.rerun()
    else:
        st.info("Click 'Generate Quiz' to create a quiz from your uploaded notes.")

# --- Quiz Answers Page ---
def quiz_answers_page():
    quiz = st.session_state.get("quiz")
    user_answers = st.session_state.get("quiz_user_answers", {})
    if not quiz or not user_answers:
        st.warning("No quiz or answers found. Please generate and take a quiz first.")
        st.session_state.page = "quiz"
        st.rerun()
    st.title("✅ Quiz Answers & Review")
    correct_count = 0
    for idx, q in enumerate(quiz):
        user_ans = user_answers.get(idx)
        correct_ans = q['answer']
        options = q['options']
        st.markdown(f"""
<div style='color:#1a237e; font-size:1.1rem; font-weight:600; margin-bottom:0.5rem;'>
    Q{idx+1}. {q['question']}
</div>
""", unsafe_allow_html=True)
        for opt_idx, opt_letter in enumerate(["A", "B", "C", "D"]):
            opt_text = options[opt_idx]
            is_correct = (opt_letter == correct_ans)
            is_user = (opt_letter == user_ans)
            if is_correct and is_user:
                st.markdown(f"<span style='color:green;font-weight:bold'>✔️ {opt_letter}: {opt_text} (Your answer, Correct)</span>", unsafe_allow_html=True)
                correct_count += 1
            elif is_correct:
                st.markdown(f"<span style='color:green;font-weight:bold'>✔️ {opt_letter}: {opt_text} (Correct Answer)</span>", unsafe_allow_html=True)
            elif is_user:
                st.markdown(f"<span style='color:red;font-weight:bold'>❌ {opt_letter}: {opt_text} (Your answer)</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"{opt_letter}: {opt_text}")
    st.success(f"You got {correct_count} out of {len(quiz)} correct!")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🏠 Home", key="ans_home"):
            st.session_state.page = "main"
            st.session_state.quiz_submitted = False
            for idx in range(len(quiz)):
                st.session_state.pop(f"quiz_q{idx}", None)
            st.rerun()
    with col2:
        if st.button("Restart Quiz", key="ans_restart_quiz"):
            st.session_state.quiz_submitted = False
            for idx in range(len(quiz)):
                st.session_state.pop(f"quiz_q{idx}", None)
            st.session_state.page = "quiz"
            st.rerun()

# --- Summarizer Page ---
def summarizer_page():
    st.title("📝 Summarizer")
    # Home button at top
    if st.button("🏠 Home", key="sum_home"):
        st.session_state.page = "main"
        st.rerun()
    if not st.session_state.openai_api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to use the summarizer.")
        st.stop()
    if not st.session_state.uploaded_text:
        st.info("Please upload a file on the home page to generate a summary.")
        st.stop()
    st.subheader("AI Summary (GPT-3.5)")
    summary_type = st.selectbox(
        "Choose summary style:",
        ["Short", "Medium", "Long", "Bullet Points"],
        key="sum_style"
    )
    if st.button("Summarize Text", key="sum_btn"):
        with st.spinner("Summarizing..."):
            try:
                client = OpenAI(api_key=st.session_state.openai_api_key)
                if summary_type == "Short":
                    style_instruction = "Write a very concise summary in 3-5 sentences."
                elif summary_type == "Medium":
                    style_instruction = "Write a clear and balanced summary in 5-8 sentences."
                elif summary_type == "Long":
                    style_instruction = "Write a detailed summary covering all main points."
                elif summary_type == "Bullet Points":
                    style_instruction = "Summarize the content using bullet points only."
                summary_prompt = f"""{style_instruction}\n\nText:\n{st.session_state.uploaded_text[:2000]}\n"""
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

# --- Main app logic ---
nav_bar()
if st.session_state.page == "main":
    main_page()
elif st.session_state.page == "flashcards":
    flashcard_page()
elif st.session_state.page == "quiz":
    quiz_page()
elif st.session_state.page == "quiz_answers":
    quiz_answers_page()
elif st.session_state.page == "summarizer":
    summarizer_page()
else:
    st.session_state.page = "main"
    st.rerun()
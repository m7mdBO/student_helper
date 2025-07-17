import streamlit as st
from openai import OpenAI

# --- Flashcard Generation (if text is available) ---
if st.session_state.get("uploaded_text", ""):
    st.subheader("🧠 Generate Flashcards (Q&A with GPT-3.5)")
    if st.button("Generate Flashcards"):
        client = OpenAI(api_key=st.session_state.openai_api_key)
        text = st.session_state.uploaded_text
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
                st.success("✅ Flashcards generated! Scroll down to review them.")

            except Exception as e:
                st.error(f"❌ Error: {e}")

# --- Flashcard Viewer Page ---
if "flashcards" not in st.session_state or not st.session_state.flashcards:
    st.warning("⚠️ No flashcards available. Please generate flashcards above.")
    st.stop()

flashcards = st.session_state.flashcards
index = st.session_state.get("flashcard_index", 0)
reveal = st.session_state.get("reveal", False)


st.title("🧠 Flashcard Viewer")
st.markdown("### ")

question, answer = flashcards[index]


# --- Styled card container ---
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

    if not reveal:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if index > 0:
                if st.button("⬅️ Previous Card"):
                    st.session_state.flashcard_index -= 1
                    st.session_state.reveal = False
                    st.rerun()
        with col2:
            if st.button("👀 Reveal Answer"):
                st.session_state.reveal = True
                st.rerun()
    else:
        # --- Answer styled card ---
        with st.container():
            st.markdown(f"""
            <div style=\"background-color:#e6f0fa; padding: 20px; border-radius: 10px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #007acc;\">
                <p style='font-size: 18px; color:#003366;'><strong>✅ Answer:</strong><br>{answer}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### ")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if index > 0:
                if st.button("⬅️ Previous Card"):
                    st.session_state.flashcard_index -= 1
                    st.session_state.reveal = False
                    st.rerun()
        with col2:
            if st.button("🔄 Back to Question"):
                st.session_state.reveal = False
                st.rerun()
        with col3:
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

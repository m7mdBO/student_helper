import streamlit as st
from openai import OpenAI

st.title("🧠 AI Summarizer (GPT-3.5)")

# Check for uploaded text and API key in session state
if not st.session_state.get("uploaded_text"):
    st.warning("⚠️ Please upload a file from the main page first.")
    st.stop()
if not st.session_state.get("openai_api_key"):
    st.warning("⚠️ Please enter your OpenAI API key in the sidebar on the main page.")
    st.stop()

text = st.session_state.uploaded_text
client = OpenAI(api_key=st.session_state.openai_api_key)

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

            summary_prompt = f"""{style_instruction}\n\nText:\n{text[:2000]}\n"""

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

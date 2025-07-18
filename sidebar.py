import streamlit as st

def sidebar_api_key():
    st.sidebar.title("🔐 API Setup")
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""
    st.session_state.openai_api_key = st.sidebar.text_input(
        "Enter your OpenAI API Key", type="password", value=st.session_state.openai_api_key
    )

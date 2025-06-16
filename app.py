import streamlit as st
import openai
import os

# Set OpenAI API key (will use secrets in Streamlit Cloud)
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

# Function to use GPT to determine if a message is a scam
def is_scam_gpt(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a scam detection expert. Answer only 'Yes' or 'No'."},
                {"role": "user", "content": f"Is this message a scam? {message}"}
            ]
        )
        reply = response.choices[0].message.content.strip().lower()
        return "yes" in reply
    except Exception as e:
        st.error(f"Error contacting OpenAI: {e}")
        return False

# Function to explain the result using GPT
def explain_scam_with_gpt(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a cybersecurity expert."},
                {"role": "user", "content": f"Explain why this message might be a scam: '{message}'"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Failed to get explanation: {e}"

# Streamlit UI
st.title("🔍 AI-Powered Scam Detector with GPT")

user_input = st.text_area("Paste your message below:", height=150)

if st.button("Analyze"):
    if user_input.strip() == "":
        st.warning("Please enter a message first.")
    else:
        scam = is_scam_gpt(user_input)
        if scam:
            st.error("⚠️ GPT thinks this message is a SCAM.")
            explanation = explain_scam_with_gpt(user_input)
            st.markdown("### 🤖 Why it might be a scam:")
            st.write(explanation)
        else:
            st.success("✅ GPT thinks this message is NOT a scam.")

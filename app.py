import streamlit as st
import os
import re
import openai
from openai import OpenAI, RateLimitError, OpenAIError

# Initialize the OpenAI client (uses OPENAI_API_KEY from env/Streamlit secrets)
client = OpenAI()

# GPT‑based scam check
def is_scam_gpt(message: str) -> bool:
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a scam detection expert. Answer only 'Yes' or 'No'."},
                {"role": "user",   "content": f"Is this message a scam? {message}"}
            ]
        )
        reply = resp.choices[0].message.content.strip().lower()
        return reply.startswith("yes")
    except RateLimitError:
        st.error("🚫 Rate limit reached. Please try again in a few seconds.")
        return False
    except OpenAIError as e:
        st.error(f"❌ OpenAI API error: {e}")
        return False

# GPT‑based explanation
def explain_scam_with_gpt(message: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert."},
                {"role": "user",   "content": f"Explain why this message might be a scam: '{message}'"}
            ]
        )
        return resp.choices[0].message.content.strip()
    except RateLimitError:
        return "🚫 Rate limit reached. Explanation unavailable."
    except OpenAIError as e:
        return f"❌ Explanation error: {e}"

# Streamlit UI
st.title("🔍 AI‑Powered Scam Detector with ChatGPT")

user_input = st.text_area("Paste your message below:", height=150)

if st.button("Analyze"):
    if not user_input.strip():
        st.warning("Please enter a message first.")
    else:
        # Rule‑based override for explicit money requests
        if re.search(r'give me \$?\d+', user_input.lower()):
            st.error("⚠️ Detected SCAM by rule: suspicious money request.")
        else:
            scam = is_scam_gpt(user_input)
            if scam:
                st.error("⚠️ GPT thinks this message is a SCAM.")
                explanation = explain_scam_with_gpt(user_input)
                st.markdown("### 🤖 Why it might be a scam:")
                st.write(explanation)
            else:
                st.success("✅ GPT thinks this message is NOT a scam.")





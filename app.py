import streamlit as st
import os
from openai import OpenAI
import re

# Initialize the OpenAI client
client = OpenAI()

# GPT‑based scam check
def is_scam_gpt(message: str) -> bool:
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You're a scam detection expert. Answer only 'Yes' or 'No'."},
            {"role": "user", "content": f"Is this message a scam? {message}"}
        ]
    )
    reply = resp.choices[0].message.content.strip().lower()
    return reply.startswith("yes")

# GPT‑based explanation
def explain_scam_with_gpt(message: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You're a cybersecurity expert."},
            {"role": "user", "content": f"Explain why this message might be a scam: '{message}'"}
        ]
    )
    return resp.choices[0].message.content.strip()

# Streamlit UI…
st.title("🔍 AI‑Powered Scam Detector with GPT")

user_input = st.text_area("Paste your message below:", height=150)
if st.button("Analyze"):
    if not user_input.strip():
        st.warning("Please enter a message first.")
    else:
        # rule‑based first
        if re.search(r'give me \$?\d+', user_input.lower()):
            st.error("⚠️ Detected SCAM by rule: suspicious money request.")
        else:
            # GPT decision
            scam = is_scam_gpt(user_input)
            if scam:
                st.error("⚠️ GPT thinks this message is a SCAM.")
                st.markdown("### 🤖 Why it might be a scam:")
                st.write(explain_scam_with_gpt(user_input))
            else:
                st.success("✅ GPT thinks this message is NOT a scam.")


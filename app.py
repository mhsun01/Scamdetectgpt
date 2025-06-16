import streamlit as st
import os, re
from openai import OpenAI, error as openai_error

# Initialize client
client = OpenAI()

def is_scam_gpt(message: str) -> bool:
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a scam detection expert. Answer only 'Yes' or 'No'."},
                {"role": "user",   "content": f"Is this message a scam? {message}"}
            ]
        )
        reply = resp.choices[0].message.content.strip().lower()
        return reply.startswith("yes")
    except openai_error.RateLimitError:
        st.error("🚫 Rate limit reached. Please try again in a few seconds.")
        return False
    except Exception as e:
        st.error(f"❌ OpenAI API error: {e}")
        return False

def explain_scam_with_gpt(message: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a cybersecurity expert."},
                {"role": "user",   "content": f"Explain why this message might be a scam: '{message}'"}
            ]
        )
        return resp.choices[0].message.content.strip()
    except openai_error.RateLimitError:
        return "🚫 Rate limit reached. Explanation unavailable."
    except Exception as e:
        return f"❌ Explanation error: {e}"

# Streamlit UI
st.title("🔍 AI‑Powered Scam Detector with GPT")

user_input = st.text_area("Paste your message below:", height=150)
if st.button("Analyze"):
    if not user_input.strip():
        st.warning("Please enter a message first.")
    else:
        # Rule override
        if re.search(r'give me \$?\d+', user_input.lower()):
            st.error("⚠️ Detected SCAM by rule: suspicious money request.")
        else:
            scam = is_scam_gpt(user_input)
            if scam:
                st.error("⚠️ GPT thinks this message is a SCAM.")
                st.markdown("### 🤖 Why it might be a scam:")
                st.write(explain_scam_with_gpt(user_input))
            else:
                st.success("✅ GPT thinks this message is NOT a scam.")



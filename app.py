import streamlit as st
import os
import re
import time
import openai
from openai import OpenAI, RateLimitError, OpenAIError

# ──────────────────────────────────────────────────────────────────────────────
# Initialize OpenAI client
# ──────────────────────────────────────────────────────────────────────────────
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI()

# ──────────────────────────────────────────────────────────────────────────────
# Caching & backoff helpers
# ──────────────────────────────────────────────────────────────────────────────
scam_cache = {}
explain_cache = {}

def call_with_backoff(fn, max_retries=5, base_delay=1, **kwargs):
    for attempt in range(max_retries):
        try:
            return fn(**kwargs)
        except RateLimitError:
            delay = base_delay * (2 ** attempt)
            st.warning(f"Rate limit reached. Retrying in {delay}s…")
            time.sleep(delay)
        except OpenAIError as e:
            st.error(f"OpenAI API error: {e}")
            return None
    st.error("🚫 Too many retries—please try again later.")
    return None

def is_scam_gpt(message: str) -> bool | None:
    if message in scam_cache:
        return scam_cache[message]
    resp = call_with_backoff(
        client.chat.completions.create,
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a scam detection expert. Answer only 'Yes' or 'No'."},
            {"role": "user",   "content": f"Is this message a scam? {message}"}
        ]
    )
    if resp is None:
        return None
    decision = resp.choices[0].message.content.strip().lower().startswith("yes")
    scam_cache[message] = decision
    return decision

def explain_scam_with_gpt(message: str) -> str:
    if message in explain_cache:
        return explain_cache[message]
    resp = call_with_backoff(
        client.chat.completions.create,
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a cybersecurity expert."},
            {"role": "user",   "content": f"Explain why this message might be a scam: '{message}'"}
        ]
    )
    text = resp.choices[0].message.content.strip() if resp else "🚫 Unable to fetch explanation."
    explain_cache[message] = text
    return text

# ──────────────────────────────────────────────────────────────────────────────
# Streamlit UI
# ──────────────────────────────────────────────────────────────────────────────
st.title("AI‑Powered Scam Detector")

user_input = st.text_area("Paste your message below:", height=150)

if st.button("Analyze"):
    if not user_input.strip():
        st.warning("Please enter a message first.")
    else:
        # Rule-based override
        if re.search(r'give me \$?\d+', user_input.lower()):
            st.error("⚠️ Detected SCAM by rule: suspicious money request.")
        else:
            scam = is_scam_gpt(user_input)
            if scam is None:
                st.warning("⚠️ GPT unavailable—using fallback detection.")
            elif scam:
                st.error("⚠️ Thinks this message is likely a SCAM.")
                explanation = explain_scam_with_gpt(user_input)
                st.markdown("### 🤖 Why it might be a scam:")
                st.write(explanation)
            else:
                st.success("✅ This message is likely NOT a scam.")

# ──────────────────────────────────────────────────────────────────────────────
# Credits (bottom‑left)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.footer {
    position: fixed;
    bottom: 10px;
    left: 20px;
    right: auto;
    font-size: 13px;
    color: #666666;
}
</style>
<div class="footer">
    Credits: Michael Sun, Ethan Soesilo, Shaurya Singh, Raul Shrestha, Adrhit Bhadauria, Rem Fellenz
</div>
""", unsafe_allow_html=True)

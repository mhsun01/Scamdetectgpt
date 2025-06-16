import streamlit as st
import os
import re
import time
import openai
from openai import OpenAI, RateLimitError, OpenAIError

# ──────────────────────────────────────────────────────────────────────────────
# Initialize OpenAI client (reads OPENAI_API_KEY from env or Streamlit secrets)
# ──────────────────────────────────────────────────────────────────────────────
client = OpenAI()

# ──────────────────────────────────────────────────────────────────────────────
# In-memory caches for GPT responses to avoid repeated calls
# ──────────────────────────────────────────────────────────────────────────────
scam_decision_cache = {}
explanation_cache = {}

# ──────────────────────────────────────────────────────────────────────────────
# Exponential backoff helper
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# GPT-based scam check with caching
# ──────────────────────────────────────────────────────────────────────────────
def is_scam_gpt(message: str) -> bool | None:
    key = ("scam", message)
    if key in scam_decision_cache:
        return scam_decision_cache[key]

    resp = call_with_backoff(
        client.chat.completions.create,
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a scam detection expert. Answer only 'Yes' or 'No'."},
            {"role": "user",   "content": f"Is this message a scam? {message}"}
        ]
    )
    if resp is None:
        # Fallback: treat as unknown
        return None

    reply = resp.choices[0].message.content.strip().lower()
    decision = reply.startswith("yes")
    scam_decision_cache[key] = decision
    return decision

# ──────────────────────────────────────────────────────────────────────────────
# GPT-based explanation with caching
# ──────────────────────────────────────────────────────────────────────────────
def explain_scam_with_gpt(message: str) -> str:
    key = ("explain", message)
    if key in explanation_cache:
        return explanation_cache[key]

    resp = call_with_backoff(
        client.chat.completions.create,
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a cybersecurity expert."},
            {"role": "user",   "content": f"Explain why this message might be a scam: '{message}'"}
        ]
    )
    if resp is None:
        explanation = "🚫 Unable to get explanation at this time."
    else:
        explanation = resp.choices[0].message.content.strip()

    explanation_cache[key] = explanation
    return explanation

# ──────────────────────────────────────────────────────────────────────────────
# Streamlit UI
# ──────────────────────────────────────────────────────────────────────────────
st.title("🔍 AI-Powered Scam Detector with Resilience")

user_input = st.text_area("Paste your message below:", height=150)

if st.button("Analyze"):
    if not user_input.strip():
        st.warning("Please enter a message first.")
    else:
        # 1️⃣ Rule-based override for explicit money requests
        if re.search(r'give me \$?\d+', user_input.lower()):
            st.error("⚠️ Detected SCAM by rule: suspicious money request.")
        else:
            # 2️⃣ Try GPT decision
            scam_decision = is_scam_gpt(user_input)
            if scam_decision is None:
                # 3️⃣ Fallback if GPT unavailable
                st.warning("⚠️ GPT unavailable—using rule-based fallback.")
                st.error("⚠️ This message may be a SCAM.")
            elif scam_decision:
                st.error("⚠️ GPT thinks this message is a SCAM.")
                explanation = explain_scam_with_gpt(user_input)
                st.markdown("### 🤖 Why it might be a scam:")
                st.write(explanation)
            else:
                st.success("✅ GPT thinks this message is NOT a scam.")

import streamlit as st
import requests
import os
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://127.0.0.1:8000/api"

st.title("📚 Smart Text Insight Pipeline (via API)")

# 1️⃣ GET predictions from API
st.header("Stored Predictions (API)")

res = requests.get(f"{API_BASE}/predictions/")
if res.status_code == 200:
    for item in res.json():
        st.subheader(f"🎬 {item['title']}")
        with st.expander("View Raw Review", expanded=False):
            st.write("**Raw:**", item['raw_text'])
        with st.expander("View Cleaned Text", expanded=False):
            st.write("**Cleaned:**", item['cleaned_text'])
        st.write(f"**Sentiment:** `{item['sentiment']}`")
        st.write("---")
else:
    st.error("Could not fetch predictions.")

# 2️⃣ POST new text to predict
st.header("Try New Prediction (API)")

new_text = st.text_area("Enter new text:")
if st.button("Predict"):
    if new_text.strip() == "":
        st.warning("Please enter text.")
    else:
        resp = requests.post(f"{API_BASE}/predict/", json={"text": new_text})
        if resp.status_code == 200:
            data = resp.json()
            st.success(f"Cleaned: {data['cleaned_text']}")
            st.success(f"Sentiment: {data['sentiment']}")
        else:
            st.error("Error predicting.")

# 3️⃣ Ask Gemini
st.header("Ask Gemini")
# GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
q = st.text_input("Ask something about your reviews:")
if st.button("Ask"):
    if q.strip() == "":
        st.warning("Type your question first.")
    else:
        res = requests.post(f"{API_BASE}/ask/", json={"question": q})
        if res.status_code == 200:
            st.success(res.json()["answer"])
        else:
            st.error("Gemini error.")
        # headers = {
        #         "Content-Type": "application/json"
        #     }
        # payload = {
        #         "contents": [
        #             {"parts": [{"text": q}]}
        #         ],
        #         "generationConfig": {
        #             "temperature": 0.7,
        #             "topK": 40,
        #             "topP": 0.95,
        #             "maxOutputTokens": 2048
        #         }
        #     }
            
        # url_with_key = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        # res = requests.post(url_with_key, json=payload, headers=headers)
        # if res.status_code == 200:
        #     response_data = res.json()
        #     if 'candidates' in response_data and len(response_data['candidates']) > 0:
        #                 answer = response_data['candidates'][0]['content']['parts'][0]['text']
        #                 st.success(answer)
        # else:
        #     st.error("Gemini error.")

st.header("📊 Sentiment Distribution")

# Call your API
res = requests.get(f"{API_BASE}/predictions/")

if res.status_code == 200:
    predictions = res.json()
    
    # Count sentiments
    counts = {}
    for item in predictions:
        label = item['sentiment'].lower()
        counts[label] = counts.get(label, 0) + 1
    
    if counts:
        labels = list(counts.keys())
        values = list(counts.values())

        fig = px.pie(
            names=labels,
            values=values,
            title="Sentiment Breakdown"
        )
        st.plotly_chart(fig)
    else:
        st.info("No predictions to display yet. Please run some predictions first!")
else:
    st.error("Could not fetch predictions for chart.")

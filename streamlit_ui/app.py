import streamlit as st
import requests
import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://127.0.0.1:8000/api"

st.title("📚 Smart Text Insight Pipeline")

st.header("Stored Predictions")

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

st.header("Try New Prediction")

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

st.header("Ask our Model")
q = st.text_input("Ask something about your reviews:")
if st.button("Ask"):
    if q.strip() == "":
        st.warning("Type your question first.")
    else:
        res = requests.post(f"{API_BASE}/ask/", json={"question": q})
        if res.status_code == 200:
            st.success(res.json()["answer"])
        else:
            st.error("Model error. Please try again.")

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

        # Create matplotlib pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Set purple background
        fig.patch.set_facecolor((9/255, 70/255, 126/255, 1.0))   
        ax.set_facecolor('purple')
        
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']  # Custom colors
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=colors[:len(labels)],
            startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}  # White boundary
        )
        
        # Customize the chart
        ax.set_title("Sentiment Breakdown", fontsize=16, fontweight='bold', color='white')
        
        # Make percentage text more readable
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Make label text white for better visibility on purple background
        for text in texts:
            text.set_color('white')
            text.set_fontweight('bold')
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        
        # Display the chart in Streamlit
        st.pyplot(fig)
        
        # Clear the figure to prevent memory issues
        plt.clf()
    else:
        st.info("No predictions to display yet. Please run some predictions first!")
else:
    st.error("Could not fetch predictions for chart.")
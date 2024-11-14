import streamlit as st
import requests
import pandas as pd
import json


st.set_page_config(page_title="AI Content Moderation Test", page_icon="🔍", layout="wide")

st.title("🛡️ SafePlace 🛡️")
st.write("Test and evaluate content moderation using Mistral AI Models. Input text,custom bad words or upload a list, pick a model, and analyze text for inappropriate content.")

# Sidebar for Model Selection
st.sidebar.header("Settings")
model = st.sidebar.selectbox(
    "Select Model",
    ("Model 1: Mistral Moderation Model", "Model 2: Mistral 8B")
)

# Main Input Section
st.subheader("🔤 Enter Text to Moderate")
text_input = st.text_area("Input Text", placeholder="Type text to analyze for moderation...")

# Custom Bad Words Input
st.subheader("🚫 Custom Bad Words")
bad_words_method = st.radio("Add custom bad words manually or upload a file:", ("Manual Entry", "Upload File"))
bad_words = []
if bad_words_method == "Manual Entry":
    bad_words = st.text_area("Enter comma-separated bad words:", placeholder="word1, word2, word3")
    bad_words = [word.strip() for word in bad_words.split(",") if word.strip()]
else:
    uploaded_file = st.file_uploader("Upload a text file with bad words (one word per line)")
    if uploaded_file:
        bad_words = [line.strip() for line in uploaded_file.read().decode("utf-8").splitlines()]


    
    
if st.button("Analyze Text"):
    # Prepare the data to send to the backend
    moderation_data = {
        "text": text_input,
        "custom_bad_words": bad_words,
        "model": model,
    }

    # Send the data to the backend
    try:
        response = requests.post('https://safe-place-mini-project.onrender.com/moderate', json=moderation_data)
        
        if response.status_code == 200:
            result = response.json()
            approved = result['approved']
            moderated_content = result['text']
            flags = result['flags']
            
            
            # Display the results
            st.subheader("📝 Moderation Results")
            if approved:
                st.success("Content Approved")
            else:
                st.error("Content Flagged")
                st.write("**Moderation Flags:**")
                for flag in flags:
                    st.write(f"- {flag}")
            
            
            st.subheader("PII masked content:")
            st.write(moderated_content)
            
        else:
            st.error("Error moderating content. Please try again.")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

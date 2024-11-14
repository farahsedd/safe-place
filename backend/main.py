from fastapi import FastAPI
import re
import os
from mistralai import Mistral
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow Svelte frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mistral API details
load_dotenv() 
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=MISTRAL_API_KEY)

# Define moderation parameters globally
moderation_params = {
    "categories": ['sexual', 'hate_and_discrimination', 'violence_and_threats',
              'dangerous_and_criminal_content', 'selfharm', 'health',
              'financial', 'law', 'pii'],
    "pii_patterns": {
        "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone_numbers": r"(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}"
    }
}


def check_moderation_with_model_1(text):
    response = client.classifiers.moderate(
        model="mistral-moderation-latest",
        inputs=[text]
    )
    return response

def check_moderation_with_model_2(text):
    prompt = "You are a content moderation model. Given the following text, please assess it for the presence of certain categories and output a series of flags (1 for presence, 0 for absence) for each category. The categories are: - sexual - hate_and_discrimination - violence_and_threats - dangerous_and_criminal_content - selfharm - health - financial - law - pii Output: Provide the flags for each category in the same order, separated by spaces. Example: Text: fuck asians. I want to kill them Response: 0 1 1 1 0 0 0 0 0 , Respond only with the list of 0s and 1s Text:"+text
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[{
            "content": prompt,
            "role": "user",
        },
    ])
    return response

def detect_custom_bad_words(text, badwords):
    masked_text = text
    for word in badwords:
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        masked_text = pattern.sub("[MASKED]", masked_text)
    masked = masked_text != text
    return masked_text, masked

def mask_pii(text, patterns):
    masked_text = text
    for label, pattern in patterns.items():
        masked_text = re.sub(pattern, "[MASKED]", masked_text)
    masked = masked_text != text
    return masked_text, masked

@app.post("/moderate")
async def moderate_content(request: dict):
    text = request.get("text", "")
    model = request.get("model", "")
    custom_bad_words = request.get("custom_bad_words", [])

    if model == "Model 1: Mistral Moderation Model":
        raw_response = check_moderation_with_model_1(text)

        moderation_result = raw_response.results[0]  

        flags = []
        for category, is_moderated in moderation_result.categories.items():
            if is_moderated:
                flags.append(category)

    elif model == "Model 2: Mistral 8B":
        raw_response = check_moderation_with_model_2(text)

        flags = raw_response.choices[0].message.content.split()
        moderation_result = {category: flag == '1' for category, flag in zip(moderation_params['categories'], flags)}

        flags = []
        for category, is_moderated in moderation_result.items():
            if is_moderated:
                flags.append(category)

    masked_text,masked = mask_pii(text, moderation_params["pii_patterns"])
    
    if masked and "pii" not in flags:
        flags.append("pii")

    masked_text, masked_badwords = detect_custom_bad_words(masked_text, custom_bad_words)
    if masked_badwords:
        flags.append("Custom Bad Words")

    if flags:
        return {"approved": False, "flags": flags, "text": masked_text}
    return {"approved": True,"flags": flags, "text": masked_text}



import feedparser
import google.generativeai as genai
import os
import sys
import requests

# --- Configuration ---
RSS_URL = "https://www.caseciter.com/rss/"
LAST_POST_FILE = "last_seen.txt"
OUTPUT_FILE = "questions_of_law.md"

def get_questions_of_law(model, title, content):
    prompt = f"""
    Analyze the following legal update and extract the specific 'Questions of Law' involved.
    Title: {title}
    Content: {content}
    
    Format the output as:
    ### {title}
    **Question of Law:** [Insert question]
    **Context:** [1-2 sentences]
    """
    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        return response.text
    except Exception as e:
        return f"AI Generation Error: {e}"

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY missing.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    
    # --- MODEL DISCOVERY & INITIALIZATION ---
    print("Initializing Gemini Model...")
    try:
        # We use the full path prefix 'models/' which is often required in newer SDK versions
        model_name = 'models/gemini-1.5-flash'
        model = genai.GenerativeModel(model_name)
        # Test call
        model.generate_content("ping")
        print(f"Successfully connected to {model_name}")
    except Exception as e:
        print(f"Warning: {model_name} failed. Listing available models...")
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation

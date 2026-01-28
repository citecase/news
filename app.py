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
        # Safety settings allow the AI to process legal/criminal case summaries without blocking
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
    
    # CHANGED TO 1.5-FLASH
    model = genai.GenerativeModel('gemini-1.5-flash')

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"Fetch Error: {e}")
        sys.exit(1)

    if not feed.entries:
        print("No entries found.")
        return

    last_link = ""
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            last_link = f.read().strip()

    new_entries = []
    for entry in feed.entries:
        if entry.link == last_link:
            break
        new_entries.append(entry)

    if not new_entries:
        print("No new posts.")
        return

    for entry in reversed(new_entries):
        print(f"Processing: {entry.title}")
        content = entry.get('summary', '')
        if 'content' in entry:
            content = entry.content[0].value

        analysis = get_questions_of_law(model, entry.title, content)

        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"{analysis}\n")
            f.write(f"*Source: {entry.link}*\n\n---\n")

    with open(LAST_POST_FILE, "w", encoding="utf-8") as f:
        f.write(feed.entries[0].link)

if __name__ == "__main__":
    main()

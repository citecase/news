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
    """Sends post content to Gemini to extract legal questions."""
    prompt = f"""
    You are a legal expert specializing in Indian Supreme Court and High Court judgments.
    Analyze the following legal update and extract the specific 'Questions of Law' involved.
    
    Title: {title}
    Content: {content}
    
    Format the output strictly as:
    ### [Case Title]
    **Question of Law:** * [Insert question here]
    
    **Legal Context:**
    [1-2 sentence summary of why this question arose]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating questions: {e}"

def main():
    # 1. API Key Check
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("CRITICAL: GEMINI_API_KEY secret is missing.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # 2. Fetch RSS Feed with User-Agent
    # (Websites often block default python-requests or feedparser headers)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"CRITICAL: Could not fetch RSS: {e}")
        sys.exit(1)

    if not feed.entries:
        print("Feed is empty or unreachable. Check RSS_URL.")
        return

    # 3. Load State (Deduplication)
    last_link = ""
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            last_link = f.read().strip()

    new_entries = []
    for entry in feed.entries:
        # Use link instead of date for better reliability in Ghost feeds
        if entry.link == last_link:
            break
        new_entries.append(entry)

    if not new_entries:
        print("No new posts since last run.")
        return

    print(f"Found {len(new_entries)} new posts. Analyzing...")

    # 4. Process and Write
    # We process in reverse (oldest new post first) so the file reads chronologically
    for entry in reversed(new_entries):
        print(f"Processing: {entry.title}")
        
        # Ghost feeds put content in 'content' list or 'summary'
        content = entry.get('summary', '')
        if 'content' in entry:
            content = entry.content[0].value

        analysis = get_questions_of_law(model, entry.title, content)

        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"{analysis}\n")
            f.write(f"*Source: {entry.link}*\n")
            f.write("\n---\n")

    # 5. Update State
    with open(LAST_POST_FILE, "w", encoding="utf-8") as f:
        f.write(feed.entries[0].link)
    
    print("Done! GitHub will now commit the changes.")

if __name__ == "__main__":
    main()

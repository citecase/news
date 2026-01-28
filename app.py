import feedparser
import google.generativeai as genai
import os
import sys

# Configuration
RSS_URL = "https://www.caseciter.com/rss/"
LAST_POST_FILE = "last_seen.txt"
OUTPUT_FILE = "questions_of_law.md"

def main():
    # 1. Check for API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment variables.")
        sys.exit(1)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"ERROR: Failed to configure Gemini AI: {e}")
        sys.exit(1)

    # 2. Parse RSS Feed
    print(f"Fetching feed from {RSS_URL}...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("Empty feed or connection issue. Check if the URL is correct.")
        return # Exit gracefully

    # 3. Handle Last Seen Timestamp
    last_timestamp = ""
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            last_timestamp = f.read().strip()
            print(f"Last processed post date: {last_timestamp}")

    new_posts = []
    for entry in feed.entries:
        if entry.published == last_timestamp:
            break
        new_posts.append(entry)

    if not new_posts:
        print("No new posts found since last run.")
        return

    print(f"Found {len(new_posts)} new posts. Processing...")

    # 4. Generate Questions
    for entry in reversed(new_posts):
        print(f"Analyzing: {entry.title}")
        prompt = f"Analyze this legal title and summary and extract the specific 'Questions of Law' involved: \nTitle: {entry.title}\nSummary: {entry.summary}"
        
        try:
            response = model.generate_content(prompt)
            questions = response.text
            
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n## {entry.title}\n")
                f.write(f"*Link: {entry.link}*\n\n")
                f.write(f"### Questions of Law:\n{questions}\n\n---\n")
        except Exception as e:
            print(f"Error processing post '{entry.title}': {e}")

    # 5. Update State
    try:
        with open(LAST_POST_FILE, "w", encoding="utf-8") as f:
            f.write(feed.entries[0].published)
        print("Successfully updated last_seen.txt")
    except Exception as e:
        print(f"Failed to save state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

import feedparser
import google.generativeai as genai
import os

# Configuration
RSS_URL = "https://www.caseciter.com/rss/"
LAST_POST_FILE = "last_seen.txt"
OUTPUT_FILE = "questions_of_law.md"

# Setup AI (Ensure GEMINI_API_KEY is in GitHub Secrets)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

def get_questions_of_law(title, summary):
    prompt = f"""
    Analyze the following legal update title and summary. 
    Identify and formulate the specific 'Questions of Law' involved in this case.
    Format them as a bulleted list.

    Title: {title}
    Summary: {summary}
    """
    response = model.generate_content(prompt)
    return response.text

def main():
    feed = feedparser.parse(RSS_URL)
    
    # Read last processed timestamp
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            last_timestamp = f.read().strip()
    else:
        last_timestamp = ""

    new_posts = []
    for entry in feed.entries:
        if entry.published == last_timestamp:
            break
        new_posts.append(entry)

    if not new_posts:
        print("No new updates.")
        return

    for entry in reversed(new_posts):
        print(f"Processing: {entry.title}")
        questions = get_questions_of_law(entry.title, entry.summary)
        
        # Save output
        with open(OUTPUT_FILE, "a") as f:
            f.write(f"\n## {entry.title}\n")
            f.write(f"*Source: {entry.link}*\n\n")
            f.write(f"### Questions of Law:\n{questions}\n\n---\n")

    # Update last seen timestamp
    with open(LAST_POST_FILE, "w") as f:
        f.write(feed.entries[0].published)

if __name__ == "__main__":
    main()

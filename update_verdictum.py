import feedparser
import requests
import os

def update_markdown():
    # Primary feed URL for Verdictum (Hocalwire CMS)
    rss_url = "https://www.verdictum.in/rss/feeds.xml"
    file_path = "verdictum.md"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(rss_url, headers=headers, timeout=20)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("No entries found. The site might be blocking the request or the feed is empty.")
            return

        # 1. Get existing links to prevent duplicates
        existing_links = set()
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Simple check for URLs in the markdown file
                import re
                existing_links = set(re.findall(r'https?://[^\s)\]]+', content))

        # 2. Extract new stories
        new_rows = []
        for entry in feed.entries:
            link = entry.link
            if link not in existing_links:
                title = entry.title.replace("|", "-").strip()
                date = entry.get('published', 'N/A')
                new_rows.append(f"| {date} | {title} | [Read More]({link}) |")

        if not new_rows:
            print("Everything is up to date. No new stories found.")
            return

        # 3. Read old table data (preserving the archive)
        old_data = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Keep only actual data rows, skipping headers
                old_data = [l.strip() for l in lines if l.startswith("|") and ":---" not in l and "Date | Title" not in l]

        # 4. Write everything back: Header + New + Old
        header = "# Verdictum - Latest Legal News\n\n| Date | Title | Link |\n| :--- | :--- | :--- |\n"
        final_table = header + "\n".join(new_rows) + "\n" + "\n".join(old_data)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_table)
        
        print(f"Success! Added {len(new_rows)} new stories.")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    update_markdown()

import feedparser
import requests
import os
import re

def update_markdown():
    # The correct feed URL you identified
    rss_url = "https://www.verdictum.in/google_feeds.xml"
    file_path = "verdictum.md"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # 1. Fetch the feed data
        response = requests.get(rss_url, headers=headers, timeout=20)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("No entries found in google_feeds.xml.")
            return

        # 2. Map existing links to prevent duplicates
        existing_links = set()
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                existing_links = set(re.findall(r'https?://[^\s)\]]+', content))

        # 3. Filter for NEW stories
        new_rows = []
        for entry in feed.entries:
            link = entry.link
            if link not in existing_links:
                title = entry.title.replace("|", "-").strip()
                # Use published date from feed or default to N/A
                date = entry.get('published', 'N/A')
                new_rows.append(f"| {date} | {title} | [Read More]({link}) |")

        if not new_rows:
            print("No new stories found to add.")
            return

        # 4. Extract old rows from the current file (preserving archive)
        old_data_rows = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    # Keep valid table rows, skip headers/separators
                    if line.startswith("|") and ":---" not in line and "Date | Title" not in line:
                        old_data_rows.append(line.strip())

        # 5. Build final file: Header -> New News -> Historical News
        header = "# Verdictum - News Archive\n\n| Date | Title | Link |\n| :--- | :--- | :--- |\n"
        final_content = header + "\n".join(new_rows) + "\n" + "\n".join(old_data_rows)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        print(f"Successfully added {len(new_rows)} new stories.")

    except Exception as e:
        print(f"Error during update: {e}")

if __name__ == "__main__":
    update_markdown()

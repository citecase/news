import feedparser
import requests
import os

def update_markdown():
    rss_url = "https://www.verdictum.in/rss/feeds.xml"
    file_path = "verdictum.md"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # 1. Fetch the Feed
        response = requests.get(rss_url, headers=headers, timeout=15)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("No entries found. site might be blocking or feed is empty.")
            return

        # 2. Read existing content to avoid duplicates
        existing_links = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
                # Store existing links to check against new entries
                existing_links = [line.split("](")[-1].split(")")[0] for line in existing_content.splitlines() if "](http" in line]

        # 3. Filter for NEW stories only
        new_rows = []
        for entry in feed.entries:
            link = entry.link
            if link not in existing_links:
                date = entry.get('published', 'N/A')
                title = entry.title.replace("|", "-").strip()
                new_rows.append(f"| {date} | {title} | [Read More]({link}) |")

        if not new_rows:
            print("No new stories found.")
            return

        # 4. Reconstruct the file: Header + New Rows + Old Rows
        header = "# Verdictum - Latest Legal News\n\n| Date | Title | Link |\n| :--- | :--- | :--- |\n"
        
        # Get existing table rows (skip the header of the old file)
        old_rows = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                old_rows = [l.strip() for l in lines if l.startswith("|") and ":---" not in l and "Date | Title" not in l]

        final_content = header + "\n".join(new_rows) + "\n" + "\n".join(old_rows)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        print(f"Added {len(new_rows)} new stories.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_markdown()

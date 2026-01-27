import feedparser
import requests
import os
import re
from datetime import datetime

def parse_date(date_str):
    """Helper to parse various RSS date formats for sorting."""
    formats = [
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S %z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return datetime.min

def update_markdown():
    # Define your sources clearly
    sources = [
        {"name": "Verdictum", "url": "https://www.verdictum.in/google_feeds.xml"},
        {"name": "LiveLaw", "url": "https://www.livelaw.in/google_feeds.xml"}
    ]
    file_path = "verdictum.md"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    all_new_stories = []
    existing_links = set()

    # 1. Map existing links to prevent duplicates
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract links to check against new entries
            existing_links = set(re.findall(r'https?://[^\s)\]]+', content))

    # 2. Fetch from all sources
    for source in sources:
        try:
            print(f"Fetching stories from {source['name']}...")
            response = requests.get(source['url'], headers=headers, timeout=20)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                link = entry.link
                if link not in existing_links:
                    title = entry.title.replace("|", "-").strip()
                    raw_date = entry.get('published', entry.get('updated', 'N/A'))
                    parsed_dt = parse_date(raw_date)
                    
                    all_new_stories.append({
                        "date": raw_date,
                        "dt_obj": parsed_dt,
                        "title": title,
                        "link": link,
                        "source": source['name']  # This explicitly sets the name
                    })
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")

    if not all_new_stories:
        print("No new stories found from any source.")
        return

    # 3. Sort new stories by date (Newest first)
    all_new_stories.sort(key=lambda x: x['dt_obj'], reverse=True)

    # 4. Format new rows with the Source column included
    new_rows = [f"| {s['date']} | **{s['source']}** | {s['title']} | [Read More]({s['link']}) |" for s in all_new_stories]

    # 5. Extract old rows from the current file
    old_data_rows = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                # This ensures we don't duplicate the headers in the archive
                if line.startswith("|") and ":---" not in line and "Date | Source" not in line:
                    old_data_rows.append(line.strip())

    # 6. Rebuild file with the correct Header
    # Added 'Source' to the header
    header = "# Legal News Archive\n\n| Date | Source | Title | Link |\n| :--- | :--- | :--- | :--- |\n"
    final_content = header + "\n".join(new_rows) + "\n" + "\n".join(old_data_rows)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    print(f"Successfully added {len(new_rows)} new stories.")

if __name__ == "__main__":
    update_markdown()

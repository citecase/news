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
        '%Y-%m-%d %H:%M:%S',
        '%d %b %Y %H:%M:%S',
        '%a, %d %b %Y %H:%M:%S %z'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return datetime.min

def update_markdown():
    # Define the four legal news sources
    sources = [
        {"name": "Verdictum", "url": "https://www.verdictum.in/google_feeds.xml"},
        {"name": "LiveLaw", "url": "https://www.livelaw.in/google_feeds.xml"},
        {"name": "Bar & Bench", "url": "https://www.barandbench.com/feed"},
        {"name": "LawBeat", "url": "https://lawbeat.in/google_feeds.xml"}
    ]
    file_path = "verdictum.md"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    all_new_stories = []
    existing_links = set()

    # 1. Map existing links in the file to prevent duplicates
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Find all existing URLs to avoid duplicates
            existing_links = set(re.findall(r'https?://[^\s)\]]+', content))

    # 2. Fetch from all four sources
    for source in sources:
        try:
            print(f"Fetching {source['name']}...")
            response = requests.get(source['url'], headers=headers, timeout=25)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                link = entry.link
                # Strip tracking parameters often found in Bar & Bench and LawBeat links
                clean_link = link.split('?')[0]
                
                if clean_link not in existing_links:
                    title = entry.title.replace("|", "-").strip()
                    raw_date = entry.get('published', entry.get('updated', 'N/A'))
                    parsed_dt = parse_date(raw_date)
                    
                    all_new_stories.append({
                        "date": raw_date,
                        "dt_obj": parsed_dt,
                        "title": title,
                        "link": clean_link,
                        "source": source['name']
                    })
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")

    if not all_new_stories:
        print("No new stories found from any source.")
        return

    # 3. Sort all new stories by date (Newest first)
    all_new_stories.sort(key=lambda x: x['dt_obj'], reverse=True)

    # 4. Format new rows with the Source explicitly mentioned
    new_rows = [f"| {s['date']} | **{s['source']}** | {s['title']} | [Read More]({s['link']}) |" for s in all_new_stories]

    # 5. Extract existing data rows to preserve the archive
    old_data_rows = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                # Keep existing table rows, skip headers/separators
                if line.startswith("|") and ":---" not in line and "Date | Source" not in line:
                    old_data_rows.append(line.strip())

    # 6. Rebuild file with the 4-column layout
    header = "# Legal News Archive\n\n| Date | Source | Title | Link |\n| :--- | :--- | :--- | :--- |\n"
    final_content = header + "\n".join(new_rows) + "\n" + "\n".join(old_data_rows)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    print(f"Successfully added {len(new_rows)} new stories from 4 combined sources.")

if __name__ == "__main__":
    update_markdown()

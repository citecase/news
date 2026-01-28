import feedparser
import requests
import os
import re
import json
from datetime import datetime
from html import unescape

def clean_html(raw_html):
    """Removes HTML tags and cleans up text for excerpts."""
    if not raw_html:
        return ""
    # Remove tags
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    # Unescape HTML entities (like &amp; or &quot;)
    cleantext = unescape(cleantext)
    # Remove extra whitespace
    cleantext = re.sub(r'\s+', ' ', cleantext).strip()
    return cleantext

def parse_date(date_str):
    """Helper to parse various RSS date formats for sorting."""
    formats = [
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S %z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S',
        '%d %b %Y %H:%M:%S'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return datetime.min

def update_feeds():
    # Define the legal news sources including LawBeat and SC judgements
    sources = [
        {"name": "Verdictum", "url": "https://www.verdictum.in/rss/feed.xml"},
        {"name": "LiveLaw", "url": "https://www.livelaw.in/rss/feed.php"},
        {"name": "Bar & Bench", "url": "https://www.barandbench.com/feed"},
        {"name": "LawBeat", "url": "https://lawbeat.in/rss/feed.xml"},
        {"name": "LiveLaw (SC)", "url": "https://www.livelaw.in/category/sc-judgments/rss/feed.xml"},
        {"name": "CaseCiter", "url": "https://caseciter.com/feed/"}
    ]
    md_file_path = "verdictum.md"
    json_file_path = "news.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    all_new_stories = []
    existing_links = set()

    # 1. Map existing links from the Markdown file to prevent duplicates
    if os.path.exists(md_file_path):
        with open(md_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            existing_links = set(re.findall(r'https?://[^\s)\]]+', content))

    # 2. Fetch from all sources
    for source in sources:
        try:
            print(f"Fetching {source['name']}...")
            response = requests.get(source['url'], headers=headers, timeout=25)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                link = getattr(entry, 'link', '')
                clean_link = link.split('?')[0]
                
                if clean_link and clean_link not in existing_links:
                    title = entry.title.replace("|", "-").strip()
                    raw_date = entry.get('published', entry.get('updated', 'N/A'))
                    parsed_dt = parse_date(raw_date)
                    
                    # Excerpt logic: Extract summary/description and clean it
                    summary_raw = entry.get('summary', entry.get('description', ''))
                    excerpt = clean_html(summary_raw)
                    
                    # Truncate for the app UI
                    if len(excerpt) > 170:
                        excerpt = excerpt[:167] + "..."
                    
                    all_new_stories.append({
                        "date": raw_date,
                        "dt_obj": parsed_dt,
                        "title": title,
                        "link": clean_link,
                        "source": source['name'],
                        "excerpt": excerpt
                    })
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")

    if not all_new_stories:
        print("No new stories found.")
        return

    # 3. Sort new stories by date (Newest first)
    all_new_stories.sort(key=lambda x: x['dt_obj'], reverse=True)

    # --- PART A: UPDATE MARKDOWN FILE ---
    new_rows = [f"| {s['date']} | **{s['source']}** | {s['title']} | [Read More]({s['link']}) |" for s in all_new_stories]
    old_data_rows = []
    if os.path.exists(md_file_path):
        with open(md_file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("|") and ":---" not in line and "Date | Source" not in line:
                    old_data_rows.append(line.strip())

    header = "# Legal News Archive\n\n| Date | Source | Title | Link |\n| :--- | :--- | :--- | :--- |\n"
    with open(md_file_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(new_rows) + "\n" + "\n".join(old_data_rows))

    # --- PART B: UPDATE JSON FILE ---
    # Prepare new stories for JSON
    json_ready_stories = []
    for s in all_new_stories:
        json_ready_stories.append({
            "title": s["title"],
            "source": s["source"],
            "date": s["date"],
            "link": s["link"],
            "excerpt": s["excerpt"]
        })
    
    # Prepend new stories to existing JSON archive
    existing_json = []
    if os.path.exists(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as f:
            try:
                existing_json = json.load(f)
            except json.JSONDecodeError:
                existing_json = []

    # Combine and limit to the 200 most recent entries
    final_json = (json_ready_stories + existing_json)[:200]
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)
    
    print(f"Updated {md_file_path} and {json_file_path} with {len(all_new_stories)} new stories.")

if __name__ == "__main__":
    update_feeds()

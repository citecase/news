import feedparser

def update_markdown():
    rss_url = "https://www.verdictum.in/feed"
    feed = feedparser.parse(rss_url)
    
    # Define the header of your markdown file
    content = "# Verdictum - Latest Legal News\n\n"
    content += "| Date | Title | Link |\n"
    content += "| :--- | :--- | :--- |\n"

    # Loop through the latest 15 entries
    for entry in feed.entries[:15]:
        # Format the date (adjust slice/format as needed)
        date = entry.published if 'published' in entry else "N/A"
        title = entry.title.replace("|", "-") # Ensure title doesn't break MD table
        link = entry.link
        
        content += f"| {date} | {title} | [Read More]({link}) |\n"

    # Write to verdictum.md
    with open("verdictum.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    update_markdown()

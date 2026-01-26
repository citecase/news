import feedparser
import urllib.request

def update_markdown():
    rss_url = "https://www.verdictum.in/rss/feeds.xml"
    
    # Use a custom User-Agent to prevent the site from blocking the request
    request = urllib.request.Request(
        rss_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    )
    
    try:
        with urllib.request.urlopen(request) as response:
            xml_data = response.read()
            feed = feedparser.parse(xml_data)
            
            if not feed.entries:
                print("No entries found. Check the RSS feed URL.")
                return

            content = "# Verdictum - Latest Legal News\n\n"
            content += "| Date | Title | Link |\n"
            content += "| :--- | :--- | :--- |\n"

            for entry in feed.entries[:15]:
                date = entry.get('published', 'N/A')
                title = entry.title.replace("|", "-") 
                link = entry.link
                content += f"| {date} | {title} | [Read More]({link}) |\n"

            with open("verdictum.md", "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully updated verdictum.md")

    except Exception as e:
        print(f"Error fetching the feed: {e}")

if __name__ == "__main__":
    update_markdown()

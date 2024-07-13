import feedparser

def get_news_by_rss(url):
    feed = feedparser.parse(url)
    entries = feed.entries
    #
    result = []
    for entry in entries:
        title = entry.title
        # description = entry.description
        pub_date = entry.published if 'published' in entry else 'No publication date available'
        result.append({"title": title, "pubDate": pub_date})
    return result
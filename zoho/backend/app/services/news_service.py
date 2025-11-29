import requests
from config import Config

class NewsService:
    @staticmethod
    def search_news(query):
        """
        Search for crypto news using CryptoPanic API.
        """
        api_key = Config.NEWS_API_KEY
        if not api_key:
            return []

        print(f"🌍 Fetching news for: {query}...")
        
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {
            "auth_token": api_key,
            "currencies": query,  # Expects SYMBOL (e.g. "BTC")
            "kind": "news",
            "public": "true"
            # REMOVED: "filter": "important" to allow more results
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if "results" not in data:
                return []
                
            news_items = []
            # Increased limit to 7 to fill the card
            for post in data["results"][:7]:
                # Clean Title
                raw_title = post.get("title", "No Title")
                clean_title = " ".join(raw_title.split())

                # Build URL
                post_url = post.get("url")
                if not post_url and "id" in post:
                    slug = post.get("slug", "news")
                    post_url = f"https://cryptopanic.com/news/{post['id']}/{slug}/"
                
                # Get Source Domain
                source = post.get("domain", "CryptoPanic")
                if isinstance(source, dict):
                    source = source.get("domain", "CryptoPanic")

                news_items.append({
                    "title": clean_title,
                    "url": post_url or "https://cryptopanic.com",
                    "source": source,
                    "published_at": post.get("published_at", "")
                })
                
            return news_items

        except Exception as e:
            print(f"❌ Failed to fetch news: {e}")
            return []

    @staticmethod
    def get_reasons_for_movement(symbol, change_pct):
        return NewsService.search_news(symbol)
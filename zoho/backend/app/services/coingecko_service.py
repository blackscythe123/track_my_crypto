import requests
import time

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    @staticmethod
    def get_prices(coin_ids):
        """
        Fetch current prices for a list of coin IDs.
        Handles large lists by batching. 
        If Rate Limit (429) is hit, STOPS immediately and returns partial results.
        """
        if not coin_ids:
            return {}
            
        # Remove duplicates and ensure lowercase
        coin_ids = list(set([cid.lower() for cid in coin_ids]))
        
        # Batch size
        BATCH_SIZE = 50 
        result = {}
        
        # Headers to mimic a browser (helps with some WAFs)
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        # Process in chunks
        for i in range(0, len(coin_ids), BATCH_SIZE):
            batch = coin_ids[i : i + BATCH_SIZE]
            ids_str = ",".join(batch)
            
            url = f"{CoinGeckoService.BASE_URL}/coins/markets"
            params = {
                "vs_currency": "inr",
                "ids": ids_str,
                "price_change_percentage": "1h,24h"
            }
            
            try:
                print(f"🔄 Fetching batch {i//BATCH_SIZE + 1} ({len(batch)} coins)...")
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                # --- NEW LOGIC: Fail Gracefully on Rate Limit ---
                if response.status_code == 429:
                    print(f"⚠️ Rate limit hit. Stopping fetch. Returning {len(result)} coins found so far.")
                    break # Stop fetching, return what we have immediately

                if response.status_code != 200:
                    print(f"⚠️ Failed batch: {response.status_code}")
                    continue

                data = response.json()
                
                for item in data:
                    result[item['id']] = {
                        'current_price': item.get('current_price', 0) or 0,
                        'price_change_percentage_1h_in_currency': item.get('price_change_percentage_1h_in_currency', 0),
                        'price_change_percentage_24h_in_currency': item.get('price_change_percentage_24h_in_currency', 0),
                        'market_cap': item.get('market_cap', 0),
                        'name': item.get('name', item['id']),
                        'symbol': item.get('symbol', '').upper()
                    }
                    
                # Be nice to the API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error fetching batch: {e}")
                
        return result

    @staticmethod
    def search_coin(query):
        """
        Search for a coin ID by name or symbol.
        """
        url = f"{CoinGeckoService.BASE_URL}/search"
        params = {"query": query}
        
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            if "coins" in data and len(data["coins"]) > 0:
                return data["coins"][0]["id"]
        except Exception as e:
            print(f"Search error: {e}")
        
        return None
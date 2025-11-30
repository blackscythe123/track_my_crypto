import sys
import os

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

from app.services.coingecko_service import CoinGeckoService

def test_coingecko():
    print("--- Testing CoinGeckoService ---")

    # 1. Test Search
    print("\n1. Testing search_coin('bitcoin')...")
    btc_id = CoinGeckoService.search_coin("bitcoin")
    print(f"Result: {btc_id}")
    
    print("\n2. Testing search_coin('solana')...")
    sol_id = CoinGeckoService.search_coin("solana")
    print(f"Result: {sol_id}")

    # 2. Test Get Prices
    ids_to_check = []
    if btc_id: ids_to_check.append(btc_id)
    if sol_id: ids_to_check.append(sol_id)
    # Add a few more to test batching/list handling
    ids_to_check.extend(['ethereum', 'dogecoin'])

    print(f"\n3. Testing get_prices({ids_to_check})...")
    prices = CoinGeckoService.get_prices(ids_to_check)
    
    if prices:
        print("Success! Retrieved prices:")
        for coin, data in prices.items():
            print(f" - {data['name']} ({data['symbol']}): ${data['current_price']}")
    else:
        print("❌ Failed to retrieve prices (or empty result).")

if __name__ == "__main__":
    test_coingecko()

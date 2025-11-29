import requests
from config import Config

class WalletService:
    BASE_URL_EVM = "https://deep-index.moralis.io/api/v2.2"
    BASE_URL_SOL = "https://solana-gateway.moralis.io"

    # Static mapping for common native tokens to CoinGecko IDs
    NATIVE_MAPPING = {
        'eth': 'ethereum',
        'bsc': 'binancecoin',
        'matic': 'matic-network',
        'avax': 'avalanche-2',
        'ftm': 'fantom',
        'arb': 'arbitrum',
        'op': 'optimism',
        'base': 'ethereum',
        'sol': 'solana',
        'btc': 'bitcoin'
    }

    # Common Token Mappings (Symbol -> CoinGecko ID)
    TOKEN_MAPPING = {
        'WETH': 'ethereum',
        'USDT': 'tether',
        'USDC': 'usd-coin',
        'DAI': 'dai',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
        'WBTC': 'bitcoin'
    }

    @staticmethod
    def get_headers():
        return {
            "accept": "application/json",
            "X-API-Key": Config.MORALIS_API_KEY
        }

    @staticmethod
    def map_token_to_coingecko(symbol, name):
        symbol = symbol.upper()
        if symbol in WalletService.TOKEN_MAPPING:
            return WalletService.TOKEN_MAPPING[symbol]
        return name.lower().replace(" ", "-")

    @staticmethod
    def fetch_wallet_balances(address, chain):
        """
        Fetch native and token balances for a given address and chain.
        """
        if not Config.MORALIS_API_KEY:
            print("Moralis API Key missing")
            return []

        holdings = []
        headers = WalletService.get_headers()

        try:
            if chain == 'sol':
                # --- SOLANA ---
                url = f"{WalletService.BASE_URL_SOL}/account/mainnet/{address}/portfolio"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                if 'nativeBalance' in data:
                    sol_amount = float(data['nativeBalance']['solana'])
                    if sol_amount > 0:
                        holdings.append({'coin_id': 'solana', 'amount': sol_amount, 'chain': chain})
                
                if 'tokens' in data:
                    for token in data['tokens']:
                        amount = float(token.get('amount', 0))
                        if amount > 0:
                            name = token.get('name', 'Unknown')
                            symbol = token.get('symbol', 'UNK')
                            coin_id = WalletService.map_token_to_coingecko(symbol, name)
                            holdings.append({'coin_id': coin_id, 'amount': amount, 'chain': chain})

            elif chain == 'btc':
                # --- BITCOIN (Via BlockCypher Free API) ---
                # Moralis EVM API does not support BTC native. Using BlockCypher as fallback.
                try:
                    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        # BlockCypher returns satoshis
                        btc_bal = data.get('final_balance', 0) / 100_000_000
                        if btc_bal > 0:
                            holdings.append({'coin_id': 'bitcoin', 'amount': btc_bal, 'chain': 'btc'})
                except Exception as e:
                    print(f"BTC Fetch Error: {e}")

            elif chain == 'btc':
                # --- BITCOIN (Via BlockCypher Free API) ---
                # Moralis EVM API does not support BTC native. Using BlockCypher as fallback.
                try:
                    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        # BlockCypher returns satoshis
                        btc_bal = data.get('final_balance', 0) / 100_000_000
                        if btc_bal > 0:
                            holdings.append({'coin_id': 'bitcoin', 'amount': btc_bal, 'chain': 'btc'})
                except Exception as e:
                    print(f"BTC Fetch Error: {e}")

            else:
                # --- EVM CHAINS ---
                chain_hex = Config.MORALIS_CHAINS.get(chain)
                if not chain_hex:
                    print(f"Chain {chain} not configured.")
                    return []

                # 1. Native Balance
                url_native = f"{WalletService.BASE_URL_EVM}/{address}/balance"
                params = {'chain': chain_hex}
                resp_native = requests.get(url_native, headers=headers, params=params)
                if resp_native.status_code == 200:
                    native_bal = float(resp_native.json().get('balance', 0)) / 10**18
                    if native_bal > 0:
                        native_id = WalletService.NATIVE_MAPPING.get(chain, 'ethereum')
                        holdings.append({'coin_id': native_id, 'amount': native_bal, 'chain': chain})

                # 2. ERC20 Token Balances
                url_tokens = f"{WalletService.BASE_URL_EVM}/{address}/erc20"
                resp_tokens = requests.get(url_tokens, headers=headers, params=params)
                if resp_tokens.status_code == 200:
                    tokens = resp_tokens.json()
                    for token in tokens:
                        decimals = int(token.get('decimals', 18))
                        raw_balance = float(token.get('balance', 0))
                        if raw_balance > 0:
                            amount = raw_balance / (10**decimals)
                            symbol = token.get('symbol', '')
                            name = token.get('name', '')
                            coin_id = WalletService.map_token_to_coingecko(symbol, name)
                            holdings.append({'coin_id': coin_id, 'amount': amount, 'chain': chain})

        except Exception as e:
            print(f"Error fetching wallet balances for {chain}:{address} - {e}")
            
        return holdings
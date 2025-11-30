from flask import Blueprint, request, jsonify
from app.models import User, Holding, Wallet, Message, db
from app.services.coingecko_service import CoinGeckoService
from app.services.news_service import NewsService
from app.services.wallet_service import WalletService
from app.services.ai_service import AIService
from config import Config
import re
import json
from datetime import datetime

bp = Blueprint('cliq', __name__, url_prefix='/api/cliq')

@bp.route('/event', methods=['POST'])
def handle_cliq_event():
    data = request.form.to_dict() if request.form else request.get_json() or {}
    print(f"DEBUG Event: {json.dumps(data, indent=2)}")

    # 1. Identify User
    user_map = data.get('user')
    if isinstance(user_map, str):
        try: user_map = json.loads(user_map)
        except: user_map = {}
    elif not isinstance(user_map, dict):
        user_map = {}

    cliq_user_id = user_map.get('id')
    if not cliq_user_id:
        return jsonify({"text": "Error: Could not identify user."})
    
    # 2. Ensure User Exists
    user = User.query.filter_by(cliq_user_id=cliq_user_id).first()
    if not user:
        user = User(cliq_user_id=cliq_user_id)
        db.session.add(user)
        db.session.commit()

    # 3. DETERMINE COMMAND SOURCE
    command = None
    args = ""
    is_ai_chat = False

    # A. Slash Command (Explicit)
    if data.get('command'):
        command = data.get('command')
        args = data.get('arguments') or data.get('args') or ''
        # Strip leading slash if present
        if command.startswith('/'): command = command[1:]

    # B. Form Submission
    elif data.get('type') == 'form_submission':
        form_data = data.get('form', {})
        command = form_data.get('name')
        args = json.dumps(form_data.get('values', {}))

    # C. Text Message (Natural Language)
    elif data.get('text'):
        raw_text = data.get('text', '').strip()
        clean_text = re.sub(r'\{@.+?\}\s*', '', raw_text).strip()
        
        if clean_text:
            # 1. Save User Message
            user_msg = Message(user_id=user.id, role='user', content=clean_text)
            db.session.add(user_msg)
            db.session.commit()

            # 2. AI Processing
            print(f"🤖 AI Analyzing: {clean_text}")
            ai_result = AIService.parse_user_intent(clean_text, user.id)
            
            if ai_result:
                command = ai_result.get('command')
                args = ai_result.get('args', '')
                is_ai_chat = True
            else:
                # Fallback if AI fails
                command = 'chat'
                args = "I'm having trouble connecting to my brain. Try `/help`."

    # 4. EXECUTE LOGIC
    if not command: return jsonify({"text": ""})

    response_json = handle_command_logic(command, args, user)
    
    # 5. Save Bot Response (Only for AI chats to keep history clean)
    if is_ai_chat and response_json.get('text'):
        bot_msg = Message(user_id=user.id, role='assistant', content=response_json['text'])
        db.session.add(bot_msg)
        db.session.commit()

    return jsonify(response_json)

def handle_command_logic(command, args, user):
    command = command.lower().strip()
    
    if command == 'price':
        return get_price(args)
    elif command == 'reasons':
        return get_reasons(args)
    elif command == 'addcoin':
        return add_coin(user, args)
    elif command == 'remove':
        return remove_coin(user, args)
    elif command == 'portfolio':
        return get_portfolio(user)
    elif command in ['link', 'linkwallet']:
        parts = args.split()
        if len(parts) >= 2:
            return link_wallet(user, parts[0], parts[1])
        return {"text": "Usage: `/linkwallet <chain> <address>`"}
    elif command in ['clear', 'clearportfolio']:
        return clear_portfolio(user)
    elif command == 'chat':
        return {"text": args} # Args contains the AI's chat response
    elif command == 'help':
        return {"text": "🤖 **Commands:**\n`/price <coin>`\n`/portfolio`\n`/addcoin <coin> <amt>`\n`/linkwallet <chain> <addr>`"}

    return {"text": f"❓ Unknown command: {command}"}

# --- LOGIC FUNCTIONS ---

def add_coin(user, args):
    if not user: return {"text": "User error."}
    
    # Smart Argument Parsing for "5 solana" vs "solana 5"
    parts = args.split()
    if len(parts) < 2:
        return {"text": "Usage: `/addcoin <coin> <amount>`"}
    
    coin_input = None
    amount = None
    
    # Try to find which part is the number
    try:
        amount = float(parts[0])
        coin_input = parts[1]
    except ValueError:
        try:
            amount = float(parts[1])
            coin_input = parts[0]
        except ValueError:
            return {"text": "Could not understand amount. Try: `addcoin btc 0.5`"}

    try:
        coin_input = coin_input.lower().strip()
        
        # 1. NORMALIZE: "sol" -> "solana"
        found_id = CoinGeckoService.search_coin(coin_input)
        coin_id = found_id if found_id else coin_input
        
        # 2. Get Symbol
        data = CoinGeckoService.get_prices([coin_id]).get(coin_id, {})
        symbol = data.get('symbol', coin_id).upper()
        
        # 3. Merge or Add
        h = Holding.query.filter_by(user_id=user.id, coin_id=coin_id, chain='manual').first()
        if h: 
            h.amount += amount
            action = "Updated"
        else:
            h = Holding(user_id=user.id, coin_id=coin_id, amount=amount, chain='manual')
            db.session.add(h)
            action = "Added"
            
        db.session.commit()
        return {"text": f"✅ {action} **{amount} {symbol}**. New Balance: **{h.amount} {symbol}**"}
    except Exception as e: 
        return {"text": f"❌ Error: {e}"}

def remove_coin(user, coin_input):
    if not user: return {"text": "User error."}
    coin_input = coin_input.lower().strip()
    
    found_id = CoinGeckoService.search_coin(coin_input)
    coin_id = found_id if found_id else coin_input
    
    h = Holding.query.filter_by(user_id=user.id, coin_id=coin_id, chain='manual').first()
    
    if h:
        db.session.delete(h)
        db.session.commit()
        return {"text": f"🗑️ Removed **{coin_id.upper()}** from portfolio."}
    else:
        return {"text": f"⚠️ Coin **{coin_id}** not found in manual holdings."}

def get_reasons(coin_input):
    if not coin_input: return {"text": "Which coin?"}
    coin_input = coin_input.lower().strip()
    
    # 1. Normalize ID
    found_id = CoinGeckoService.search_coin(coin_input)
    coin_id = found_id if found_id else coin_input
    
    # 2. Get Symbol for Search
    data = CoinGeckoService.get_prices([coin_id]).get(coin_id, {})
    symbol = data.get('symbol', '').upper()
    search_query = symbol if symbol else coin_id.upper()
    
    reasons = NewsService.search_news(search_query)
    
    if not reasons: 
        return {"text": f"No news found for **{search_query}**."}
    
    lines = [f"📰 **News for {search_query}:**"]
    for r in reasons:
        lines.append(f"• [{r['title']}]({r['url']})")
    return {"text": "\n".join(lines)}

def get_price(coin):
    coin = coin.lower().strip()
    found_id = CoinGeckoService.search_coin(coin)
    if found_id: coin = found_id
    
    data = CoinGeckoService.get_prices([coin]).get(coin)
    if not data: return {"text": f"❌ Coin '{coin}' not found."}
    
    price = data['current_price']
    change = data.get('price_change_percentage_24h_in_currency', 0)
    emoji = "📈" if change >= 0 else "📉"
    
    return {
        "text": f"💵 **{data.get('name').title()} ({data.get('symbol').upper()})**: ${price:,.2f} ({change:.2f}% {emoji})"
    }

def get_portfolio(user):
    if not user or not user.holdings.count():
        return {"text": "📉 Your portfolio is empty. Use `/addcoin` or `/linkwallet` to start."}
        
    report = [f"📊 **Portfolio Summary**"]
    total_value = 0
    
    # Ensure IDs are lowercase for API lookup
    coin_ids = [h.coin_id.lower() for h in user.holdings]
    prices = CoinGeckoService.get_prices(coin_ids)
    
    # Explicitly includes HOLDING (Amount)
    report.append(f"`{'COIN':<8} | {'NET':<5} | {'PRICE':<9} | {'HOLDING':<9} | {'VALUE':<10}`")
    
    for h in user.holdings:
        # Lookup using lowercase ID
        price_data = prices.get(h.coin_id.lower(), {})
        price = price_data.get('current_price', 0)
        value = h.amount * price
        total_value += value
        
        symbol = price_data.get('symbol', h.coin_id).upper()
        chain = h.chain.upper() if h.chain else "MAN"
        
        if value > 0.01 or h.chain == 'manual':
            report.append(f"`{symbol:<8} | {chain:<5} | ${price:<9,.2f} | {h.amount:<9.2f} | ${value:<10,.2f}`")

    report.append(f"\n💰 **Total Value: ₹{total_value:,.2f}**")
    return {"text": "\n".join(report)}

def clear_portfolio(user):
    if not user: return {"text": "User error."}
    Holding.query.filter_by(user_id=user.id).delete()
    Wallet.query.filter_by(user_id=user.id).delete()
    Message.query.filter_by(user_id=user.id).delete() # Clear chat history too
    db.session.commit()
    return {"text": "🗑️ Portfolio and chat history cleared."}

def link_wallet(user, chain, address):
    if not user: return {"text": "User error."}
    if chain not in Config.SUPPORTED_CHAINS:
        return {"text": f"❌ Chain '{chain}' not supported. Try: {', '.join(Config.SUPPORTED_CHAINS)}"}
        
    existing = Wallet.query.filter_by(user_id=user.id, address=address).first()
    if existing: return {"text": "⚠️ Wallet already linked."}
    
    w = Wallet(user_id=user.id, address=address, chain=chain, name=f"{chain} Wallet")
    db.session.add(w)
    db.session.commit()
    
    # Trigger immediate sync
    try:
        holdings = WalletService.fetch_wallet_balances(address, chain)
        count = 0
        for h_data in holdings:
            # Check if holding exists
            h = Holding.query.filter_by(user_id=user.id, coin_id=h_data['coin_id'], chain=chain).first()
            if h:
                h.amount = h_data['amount']
            else:
                h = Holding(user_id=user.id, coin_id=h_data['coin_id'], amount=h_data['amount'], chain=chain)
                db.session.add(h)
            count += 1
        db.session.commit()
        return {"text": f"✅ Wallet {address[:6]}... linked! Found {count} assets."}
    except Exception as e:
        print(f"Sync Error: {e}")
        return {"text": f"✅ Wallet linked, but sync failed: {e}"}
from flask import Blueprint, request, jsonify
from app.models import User, Holding, Price, Alert, Wallet, db
from app.services.coingecko_service import CoinGeckoService
from app.services.volatility_service import VolatilityService
from app.services.news_service import NewsService
from app.services.zoho_service import ZohoService
from app.services.wallet_service import WalletService
from config import Config
from datetime import datetime, timedelta
import os
import time

bp = Blueprint('cron', __name__, url_prefix='/api/cron')

@bp.route('/run-tasks', methods=['GET'])
def run_scheduled_tasks():
    """
    Endpoint to trigger background tasks (Wallet Sync, Price Check, Alerts).
    Protected by a simple key check.
    Usage: GET /api/cron/run-tasks?key=<YOUR_SECRET_KEY>
    """
    # Security Check
    api_key = request.args.get('key')
    # Use a specific CRON_KEY env var, or fallback to SECRET_KEY
    expected_key = Config.CRON_SECRET
    
    if not expected_key or api_key != expected_key:
        return jsonify({"error": "Unauthorized"}), 401

    results = {
        "wallets_synced": 0,
        "prices_checked": 0,
        "alerts_sent": 0,
        "errors": []
    }

    # ---------------------------------------------------------
    # 1. SYNC WALLETS
    # ---------------------------------------------------------
    try:
        wallets = Wallet.query.all()
        for wallet in wallets:
            holdings_data = WalletService.fetch_wallet_balances(wallet.address, wallet.chain)
            if holdings_data:
                for item in holdings_data:
                    coin_id = item['coin_id']
                    amount = item['amount']
                    chain = item['chain']
                    
                    # Update or Create Holding
                    holding = Holding.query.filter_by(
                        user_id=wallet.user_id, 
                        coin_id=coin_id, 
                        chain=chain
                    ).first()
                    
                    if holding:
                        holding.amount = amount
                    else:
                        holding = Holding(
                            user_id=wallet.user_id, 
                            coin_id=coin_id, 
                            amount=amount, 
                            chain=chain
                        )
                        db.session.add(holding)
                
                wallet.last_synced_at = datetime.utcnow()
                results["wallets_synced"] += 1
                # Sleep briefly to avoid rate limits if many wallets
                time.sleep(0.5)
        db.session.commit()
    except Exception as e:
        error_msg = f"Wallet Sync Error: {str(e)}"
        print(error_msg)
        results["errors"].append(error_msg)

    # ---------------------------------------------------------
    # 2. CHECK PRICES & VOLATILITY
    # ---------------------------------------------------------
    try:
        # Get all unique coins tracked
        holdings = Holding.query.with_entities(Holding.coin_id).distinct().all()
        all_coin_ids = [h.coin_id for h in holdings]
        
        if all_coin_ids:
            # Fetch prices (Service handles batching)
            prices = CoinGeckoService.get_prices(all_coin_ids)
            results["prices_checked"] = len(prices)
            
            for coin_id, data in prices.items():
                # Update Price DB
                price_record = Price.query.get(coin_id)
                if not price_record:
                    price_record = Price(coin_id=coin_id)
                    db.session.add(price_record)
                    
                price_record.last_price = data['current_price']
                price_record.last_change_pct_1h = data.get('price_change_percentage_1h_in_currency', 0)
                price_record.last_change_pct_24h = data.get('price_change_percentage_24h_in_currency', 0)
                
                # Check Volatility
                volatility_alerts = VolatilityService.check_volatility(data)
                if volatility_alerts:
                    # Fetch reasons (optional, can be skipped to save API calls)
                    reasons = []
                    # DISABLED to save API calls
                    # try:
                    #     reasons = NewsService.get_reasons_for_movement(coin_id, volatility_alerts[0]['change'])
                    # except: pass
                    
                    # Notify Users
                    users_holding = User.query.join(Holding).filter(Holding.coin_id == coin_id).all()
                    for user in users_holding:
                        if not user.default_channel_id: continue
                        
                        for alert in volatility_alerts:
                            # Check Cooldown: Don't spam if we alerted this user about this coin recently (e.g. 6 hours)
                            last_alert = Alert.query.filter_by(
                                user_id=user.id, 
                                coin_id=coin_id
                            ).order_by(Alert.timestamp.desc()).first()
                            
                            if last_alert and (datetime.utcnow() - last_alert.timestamp) < timedelta(hours=6):
                                continue

                            # Save Alert
                            new_alert = Alert(
                                user_id=user.id,
                                coin_id=coin_id,
                                price_change_pct=alert['change'],
                                alert_message=alert['message']
                            )
                            db.session.add(new_alert)
                            
                            # Send Message
                            try:
                                payload = ZohoService.format_alert_message(coin_id, alert, reasons, data['current_price'])
                                ZohoService.send_message(user.default_channel_id, payload)
                                results["alerts_sent"] += 1
                            except Exception as e:
                                print(f"Send Error: {e}")
            
            db.session.commit()
            
    except Exception as e:
        error_msg = f"Price Check Error: {str(e)}"
        print(error_msg)
        results["errors"].append(error_msg)
        return jsonify({"status": "partial_error", "results": results}), 500

    return jsonify({"status": "success", "results": results})

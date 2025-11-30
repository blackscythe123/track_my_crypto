from flask import Blueprint, jsonify
from app.models import User
from app.services.coingecko_service import CoinGeckoService

bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')

@bp.route('/<user_id>', methods=['GET'])
def get_portfolio_data(user_id):
    user = User.query.filter_by(cliq_user_id=user_id).first()
    
    if not user:
        return jsonify({"total_value": 0, "holdings": []})

    holdings_data = []
    total_value = 0
    
    if user.holdings.count() > 0:
        coin_ids = [h.coin_id for h in user.holdings]
        prices = CoinGeckoService.get_prices(coin_ids)
        
        for h in user.holdings:
            price = prices.get(h.coin_id, {}).get('current_price', 0)
            value = h.amount * price
            total_value += value
            
            holdings_data.append({
                "coin": h.coin_id,
                "current_price": price,
                "amount": h.amount,
                "value": value,
                "chain": h.chain
            })

    return jsonify({
        "total_value": total_value,
        "holdings": holdings_data
    })

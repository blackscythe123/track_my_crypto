from config import Config

class VolatilityService:
    @staticmethod
    def check_volatility(coin_data):
        """
        Check if the coin data indicates high volatility.
        Returns a list of alerts.
        """
        alerts = []
        coin_id = coin_data.get('id') # This might need to be passed separately if data is just metrics
        
        change_1h = coin_data.get('price_change_percentage_1h_in_currency', 0)
        change_24h = coin_data.get('price_change_percentage_24h_in_currency', 0)
        
        if abs(change_1h) >= Config.VOLATILITY_1H_THRESHOLD:
            alerts.append({
                'type': '1h_volatility',
                'change': change_1h,
                'message': f"{'UP' if change_1h > 0 else 'DOWN'} {change_1h:.2f}% in 1h"
            })
            
        if abs(change_24h) >= Config.VOLATILITY_24H_THRESHOLD:
            alerts.append({
                'type': '24h_volatility',
                'change': change_24h,
                'message': f"{'UP' if change_24h > 0 else 'DOWN'} {change_24h:.2f}% in 24h"
            })
            
        return alerts

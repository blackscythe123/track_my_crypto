import requests
from config import Config

class ZohoService:
    """
    Service to interact with Zoho Cliq REST API.
    Used for sending messages from the backend (worker) to the bot/channel.
    """
    BASE_URL = "https://cliq.zoho.com/api/v2"

    @staticmethod
    def send_message(channel_id, message_data):
        """
        Send a message to a specific channel or user (DM) via the Bot.
        Note: To send to a user DM, channel_id should be the DM channel ID or use a different endpoint.
        For simplicity, we assume channel_id is valid for the bot to post to.
        """
        if not Config.BOT_TOKEN or not Config.BOT_ID:
            print("Bot credentials not configured.")
            return False

        # Endpoint: https://cliq.zoho.com/api/v2/bots/{bot_unique_name}/message?zapikey={bot_token}
        # Or if sending to a specific channel: 
        # https://cliq.zoho.com/api/v2/channels/{channel_id}/message?zapikey={bot_token}
        # But usually bots post to the channel context they are in.
        
        # If we have a channel_id (chat_id), we can target it.
        url = f"{ZohoService.BASE_URL}/channels/{channel_id}/message"
        
        params = {
            "zapikey": Config.BOT_TOKEN
        }
        
        # message_data should be the JSON body expected by Zoho Cliq
        try:
            response = requests.post(url, params=params, json=message_data)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Zoho message: {e}")
            if hasattr(e, 'response') and e.response:
                print(e.response.text)
            return False

    @staticmethod
    def format_alert_message(coin, alert, reasons, current_price):
        change_emoji = "📈" if alert['change'] > 0 else "📉"
        
        slides = [
            {
                "type": "label",
                "data": [
                    {"label": "Price", "value": f"₹{current_price}"},
                    {"label": "Change", "value": f"{alert['change']:.2f}%"}
                ]
            }
        ]
        
        if reasons:
            reasons_text = "\n".join([f"• [{r['title']}]({r['url']})" for r in reasons[:3]])
            slides.append({
                "type": "text",
                "title": "Possible Reasons",
                "data": reasons_text
            })
        
        return {
            "text": f"🚨 **{coin.upper()} {alert['message']}**",
            "card": {
                "title": f"{change_emoji} {coin.upper()} Alert",
                "theme": "modern-inline"
            },
            "slides": slides
        }

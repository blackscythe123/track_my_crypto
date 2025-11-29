import google.generativeai as genai
import json
import re
from config import Config
from app.models import Message

class AIService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None and Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            try:
                cls._model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception:
                print("⚠️ Switching to gemini-pro model")
                cls._model = genai.GenerativeModel('gemini-pro')
        return cls._model

    @staticmethod
    def parse_user_intent(user_text, user_id):
        """
        Uses Gemini to analyze natural language and map it to a bot command.
        Includes chat history for context.
        """
        model = AIService.get_model()
        if not model:
            print("⚠️ Gemini API Key missing. AI features disabled.")
            return None

        # 1. Fetch Chat History (Last 6 messages)
        history_objs = Message.query.filter_by(user_id=user_id).order_by(Message.timestamp.desc()).limit(6).all()
        # Reverse to chronological order
        history_objs.reverse()
        
        history_str = ""
        for msg in history_objs:
            role_name = "User" if msg.role == 'user' else "Bot"
            history_str += f"{role_name}: {msg.content}\n"

        # 2. Construct Prompt
        prompt = f"""
        You are the brain of a Crypto Portfolio Bot.
        Your job is to translate user natural language into a JSON command based on the conversation history.

        AVAILABLE COMMANDS:
        - "price": Check price. Args: coin name (e.g., "bitcoin", "eth").
        - "reasons": Explain price movement/news. Args: coin name.
        - "addcoin": Add to portfolio. Args: "coin amount" (e.g., "btc 0.5").
        - "portfolio": View portfolio. Args: "" (empty string).
        - "linkwallet": Link wallet. Args: "chain address" (e.g., "eth 0x123...").
        - "clear": Clear/reset data. Args: "".
        - "help": User asks for help. Args: "".
        - "chat": General greeting/unclear. Args: A short, friendly reply text.

        RULES:
        1. Return ONLY valid JSON. No markdown (```json), no explanations.
        2. Infer context from history (e.g., "how much is it?" refers to the coin mentioned previously).
        3. "add to my wallet" or "link address" -> command: "linkwallet".
        4. "add 5 btc" or "buy 10 eth" -> command: "addcoin".
        5. If the user says "hello", return command "chat" with args "Hello! I am your Crypto Bot.".
        6. If the user provides a wallet address (starts with 0x, 1, 3, bc1, etc) without a chain, infer the chain:
           - Starts with "0x" -> "eth" (default)
           - Starts with "1", "3", "bc1" -> "btc"
           - Starts with "T" -> "trx" (if supported)
           - Base58 (Solana) -> "sol"
           Then return command "linkwallet" with args "chain address".

        CONVERSATION HISTORY:
        {history_str}
        
        CURRENT INPUT: "{user_text}"
        
        OUTPUT JSON:
        """

        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Clean Markdown
            raw_text = re.sub(r"^```json\s*", "", raw_text, flags=re.MULTILINE)
            raw_text = re.sub(r"\s*```$", "", raw_text, flags=re.MULTILINE)
            
            parsed = json.loads(raw_text)
            print(f"🧠 AI Decided: {parsed}")
            return parsed

        except Exception as e:
            print(f"❌ AI Parsing Error: {e}")
            return None
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Database Config for Render (Postgres)
    # Render uses 'postgres://' but SQLAlchemy requires 'postgresql://'
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = database_url or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    COINGECKO_API_BASE = os.environ.get('COINGECKO_API_BASE', 'https://api.coingecko.com/api/v3')
    COINGECKO_API_KEY = os.environ.get('COINGECKO_API_KEY')
    
    # AI Config
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Zoho Cliq Bot Config
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    BOT_ID = os.environ.get('BOT_ID')
    
    # Volatility Thresholds
    VOLATILITY_1H_THRESHOLD = float(os.environ.get('VOLATILITY_1H_THRESHOLD', 3.0))
    VOLATILITY_24H_THRESHOLD = float(os.environ.get('VOLATILITY_24H_THRESHOLD', 5.0))
    
    # Moralis Config
    MORALIS_API_KEY = os.environ.get('MORALIS_API_KEY')
    # Map friendly names to Moralis Hex Chain IDs
    MORALIS_CHAINS = {
        'eth': '0x1',
        'bsc': '0x38',
        'matic': '0x89',
        'avax': '0xa86a',
        'ftm': '0xfa',
        'arb': '0xa4b1',
        'op': '0xa',
        'base': '0x2105'
    }
    
    # Added 'btc' to supported chains
    SUPPORTED_CHAINS = list(MORALIS_CHAINS.keys()) + ['sol', 'btc']
    
    @staticmethod
    def validate():
        missing = []
        if not Config.BOT_TOKEN: missing.append('BOT_TOKEN')
        if not Config.BOT_ID: missing.append('BOT_ID')
        if not Config.GEMINI_API_KEY: missing.append('GEMINI_API_KEY')
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
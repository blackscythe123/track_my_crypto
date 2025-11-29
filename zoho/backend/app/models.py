from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    cliq_user_id = db.Column(db.String(64), unique=True, nullable=False)
    # Store the channel ID where the user interacts with the bot, to send alerts back
    default_channel_id = db.Column(db.String(64), nullable=True) 
    holdings = db.relationship('Holding', backref='owner', lazy='dynamic')
    alerts = db.relationship('Alert', backref='user', lazy='dynamic')
    wallets = db.relationship('Wallet', backref='owner', lazy='dynamic')
    messages = db.relationship('Message', backref='user', lazy='dynamic')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(20), nullable=False) # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Wallet(db.Model):
    __tablename__ = 'wallets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    address = db.Column(db.String(128), nullable=False)
    chain = db.Column(db.String(20), default='eth')
    name = db.Column(db.String(50), nullable=True) # User-friendly name
    last_synced_at = db.Column(db.DateTime, default=datetime.utcnow)

class Holding(db.Model):
    __tablename__ = 'holdings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    coin_id = db.Column(db.String(64), nullable=False)
    chain = db.Column(db.String(20), default='eth') # Network awareness
    amount = db.Column(db.Float, nullable=False)

    # Composite Index for faster lookups when users scale
    __table_args__ = (db.Index('idx_user_coin_chain', 'user_id', 'coin_id', 'chain'),)

class Price(db.Model):
    __tablename__ = 'prices'
    coin_id = db.Column(db.String(64), primary_key=True)
    last_price = db.Column(db.Float)
    last_change_pct_1h = db.Column(db.Float)
    last_change_pct_24h = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    coin_id = db.Column(db.String(64))
    price_change_pct = db.Column(db.Float)
    alert_message = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

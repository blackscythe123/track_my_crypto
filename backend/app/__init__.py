from flask import Flask
from flask_cors import CORS
from config import Config
from app.extensions import db, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models to ensure they are registered with SQLAlchemy
    from app import models

    from app.routes import cliq, portfolio, cron
    app.register_blueprint(cliq.bp)
    app.register_blueprint(portfolio.bp)
    app.register_blueprint(cron.bp)

    @app.route('/')
    def index():
        return "Zoho Cliq Crypto Backend is Running!"

    return app

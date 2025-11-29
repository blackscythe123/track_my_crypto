from app import create_app, db
from app import models

app = create_app()
with app.app_context():
    print("Tables in metadata:", db.Model.metadata.tables.keys())

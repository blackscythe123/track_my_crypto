from app import create_app, db
from flask_migrate import upgrade

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # This creates tables if they don't exist (Safety net)
        db.create_all()
        # Then run migrations to ensure they are up to date
        try:
            upgrade()
        except Exception as e:
            print(f"Migration Error (ignored): {e}")
            
    app.run(debug=True, port=5000)

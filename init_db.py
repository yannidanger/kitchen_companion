from app import create_app, db
from app.models import Recipe, Ingredient

app = create_app()

with app.app_context():
    print("Creating all tables...")
    db.create_all()  # Create all tables based on the models
    print("Tables created successfully.")

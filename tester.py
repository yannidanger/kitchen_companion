from app import create_app, db
from app.database_utils import seed_sections  # Adjust import path as needed

# Create the app instance
app = create_app()

if __name__ == "__main__":
    with app.app_context():
        print("Creating all tables...")
        db.create_all()  # Creates all tables based on models in `models.py`
        print("Tables created successfully.")

        # Seed the default sections
        seed_sections()
        print("Default sections seeded.")

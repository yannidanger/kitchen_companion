from app import create_app, db
from app.models import Recipe

app = create_app()

with app.app_context():
    print("Inspecting database...")
    recipes = Recipe.query.all()

    if not recipes:
        print("No recipes found. Populating database with initial data...")
        sample_recipes = [
            Recipe(name="Spaghetti Bolognese", description="Classic Italian pasta dish with rich meat sauce."),
            Recipe(name="Chicken Curry", description="Spicy and flavorful chicken curry."),
            Recipe(name="Vegetable Stir Fry", description="Quick and healthy mixed vegetable stir fry.")
        ]
        db.session.add_all(sample_recipes)
        db.session.commit()
        print("Database populated with sample recipes.")
    else:
        print(f"Found {len(recipes)} recipe(s) in the database.")

    print("Database inspection complete.")

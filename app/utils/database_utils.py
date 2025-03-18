from app.models import db, Recipe, Ingredient, StoreSection

def add_recipe_to_database(name, instructions, ingredients):
    """
    Add a new recipe with its ingredients to the database.
    """
    try:
        recipe = Recipe(name=name, instructions=instructions)
        db.session.add(recipe)
        db.session.commit()  # Commit to generate recipe ID

        for ingredient_data in ingredients:
            ingredient = Ingredient(
                recipe_id=recipe.id,
                food_name=ingredient_data['food_name'],
                quantity=ingredient_data['quantity'],
                unit=ingredient_data['unit'],
                size=ingredient_data['size'],
                descriptor=ingredient_data['descriptor'],
                additional_descriptor=ingredient_data['additional_descriptor']
            )
            db.session.add(ingredient)

        db.session.commit()  # Commit all ingredients
    except Exception as e:
        db.session.rollback()
        print(f"Error adding recipe: {e}")
        raise

def seed_sections():
    DEFAULT_SECTIONS = [
        "Pharmacy Section",
        "Bakery Section",
        "Deli",
        "Produce Section",
        "Dairy Section",
        "Aisle 1: Breakfast Items",
        "Aisle 2: Baby Products",
        "Aisle 3: Health & Beauty",
        "Aisle 4: Soup",
        "Aisle 5: Ethnic Foods",
        "Aisle 6: Candy",
        "Aisle 7: Condiments & Baking",
        "Aisle 8: Canned, Dry, Sauces",
        "Aisle 9: Pet Supplies, Magazines, Batteries",
        "Aisle 10: Cleaning Supplies",
        "Aisle 11: Paper Goods",
        "Aisle 12: Bread, Water & Snacks",
        "Aisle 13: Frozen Foods Section",
        "Seafood Section",
        "Meat Section",
        "Aisle 14: Cheeses, Hotdogs, Frozen Meals",
        "Aisle 15: Dessert Aisle",
        "Alcohol Section",
        "Uncategorized"
    ]

    for order, name in enumerate(DEFAULT_SECTIONS, start=1):
        section = StoreSection(name=name, order=order)
        db.session.add(section)
    db.session.commit()
    print("Default sections seeded.")
    print("Default sections added to SQLite.")
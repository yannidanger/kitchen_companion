from app.models import db, Recipe, Ingredient

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

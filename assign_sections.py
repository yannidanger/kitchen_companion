from app import create_app, db
from app.models import Ingredient, Section, IngredientSection

app = create_app()
with app.app_context():
    # Define the mapping of ingredient names to sections
    INGREDIENT_SECTION_MAPPING = {
        "milk": "Dairy Section",
        "cheese": "Dairy Section",
        "butter": "Dairy Section",
        "yogurt": "Dairy Section",
        "eggs": "Dairy Section",
        "bread": "Bakery Section",
        "flour": "Aisle 7: Condiments & Baking",
        "sugar": "Aisle 7: Condiments & Baking",
        "salt": "Aisle 7: Condiments & Baking",
        "pepper": "Aisle 7: Condiments & Baking",
        "chicken": "Meat Section",
        "beef": "Meat Section",
        "fish": "Seafood Section",
        "apple": "Produce Section",
        "banana": "Produce Section",
        "carrot": "Produce Section",
        "lettuce": "Produce Section",
        "potato": "Produce Section",
        "cereal": "Aisle 1: Breakfast Items",
        "juice": "Aisle 12: Bread, Water & Snacks",
        "ice cream": "Aisle 15: Dessert Aisle"
    }

    # Assign ingredients to sections
    for ingredient in Ingredient.query.all():
        ingredient_name = ingredient.item_name.lower()

        # Find a section based on mapping
        section_name = None
        for key in INGREDIENT_SECTION_MAPPING.keys():
            if key in ingredient_name:
                section_name = INGREDIENT_SECTION_MAPPING[key]
                break

        if section_name:
            section = Section.query.filter_by(name=section_name).first()
            if section and not IngredientSection.query.filter_by(ingredient_id=ingredient.id).first():
                new_mapping = IngredientSection(ingredient_id=ingredient.id, section_id=section.id)
                db.session.add(new_mapping)

    db.session.commit()
    print("✅ Ingredients successfully assigned to sections!")

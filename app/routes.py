from fractions import Fraction
import logging
from flask import Blueprint, jsonify, request, render_template, current_app
from app.utils import parse_ingredients  # Importing the missing function
from app import db
from app.utils import convert_to_base_unit
from datetime import datetime
from app.models import Store, Section, IngredientSection, Ingredient, Recipe, WeeklyPlan, MealSlot, Recipe, RecipeComponent, RecipeIngredient
print("Recipe model is recognized:", Recipe)
from collections import defaultdict
from typing import Optional



sub_recipes_bp = Blueprint('sub_recipes', __name__, url_prefix='/api/sub_recipes')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a Blueprint for recipes
recipes_routes = Blueprint('recipes_routes', __name__)

# Create a Blueprint for meal planning
meal_planner_routes = Blueprint('meal_planner_routes', __name__)
logger.debug("Registering meal_planner_routes Blueprint")

# Create the blueprint
store_routes = Blueprint('store_routes', __name__)

ingredient_routes = Blueprint('ingredient_routes', __name__)

grocery_routes = Blueprint('grocery_routes', __name__)

DEFAULT_SECTIONS = [
    "Pharmacy Section", "Bakery Section", "Deli", "Produce Section",
    "Dairy Section", "Aisle 1: Breakfast Items", "Aisle 2: Baby Products",
    "Aisle 3: Health & Beauty", "Aisle 4: Soup", "Aisle 5: Ethnic Foods",
    "Aisle 6: Candy", "Aisle 7: Condiments & Baking", "Aisle 8: Canned, Dry, Sauces",
    "Aisle 9: Pet Supplies, Magazines, Batteries", "Aisle 10: Cleaning Supplies",
    "Aisle 11: Paper Goods", "Aisle 12: Bread, Water & Snacks",
    "Aisle 13: Frozen Foods Section", "Seafood Section", "Meat Section",
    "Aisle 14: Cheeses, Hotdogs, Frozen Meals", "Aisle 15: Dessert Aisle",
    "Alcohol Section"
]

# Define a fixed mapping of ingredients to store sections
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
}


def format_grocery_list_with_default_sections(ingredients):
    from collections import defaultdict  # Ensure you have the import
    grouped = defaultdict(list)
    for item in ingredients:
        section = item.get('section')
        if not section or section not in DEFAULT_SECTIONS:
            section = 'Uncategorized'
        logger.debug(f"Item: {item}, Section: {section}")
        grouped[section].append(item)

    for section in DEFAULT_SECTIONS:
        if section not in grouped:
            grouped[section] = []
    logger.debug(f"Formatted grocery list: {grouped}")
    return [{"section": section, "items": grouped[section]} for section in DEFAULT_SECTIONS if section in grouped]


@recipes_routes.route('/recipes', methods=['GET'])
def recipes():
    return render_template('recipes.html')

@recipes_routes.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    return jsonify({
        **recipe.to_dict(),
        'ingredients': [ri.to_dict() for ri in recipe.ingredients]
    })

# Update the add_recipe route in routes.py (around line 97)
@recipes_routes.route('/api/recipes', methods=['POST'])
def add_recipe():
    data = request.get_json()
    logger.debug(f"Recipe data received: {data}")

    # Create or update recipe
    recipe = Recipe.query.get(data.get('id')) if data.get('id') else Recipe()
    recipe.name = data['name']
    recipe.cook_time = int(data['cook_time']) if data['cook_time'] else None
    recipe.servings = int(data['servings']) if data['servings'] else None
    recipe.instructions = data['instructions']

    if not recipe.id:
        db.session.add(recipe)
        db.session.flush()

    # Clear existing ingredients and components
    RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
    RecipeComponent.query.filter_by(recipe_id=recipe.id).delete()

    # Process ingredients
    for ingredient_data in data['ingredients']:
        # Check if this is a sub-recipe reference
        sub_recipe_id = ingredient_data.get('sub_recipe_id')
        if sub_recipe_id:
            # Add as a component (sub-recipe)
            component = RecipeComponent(
                recipe_id=recipe.id,
                sub_recipe_id=sub_recipe_id,
                quantity=float(ingredient_data['quantity']) if ingredient_data.get('quantity') else 1.0
            )
            db.session.add(component)
        else:
            # Regular ingredient
            ingredient_name = ingredient_data['item_name']
            ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
            if not ingredient:
                ingredient = Ingredient(name=ingredient_name)
                db.session.add(ingredient)
                db.session.flush()

            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=float(ingredient_data['quantity']) if ingredient_data.get('quantity') else None,
                unit=ingredient_data.get('unit', '')
            )
            db.session.add(recipe_ingredient)

    db.session.commit()

    return jsonify(recipe.to_dict()), 201


# Validation function
def validate_recipe_payload(data):
    required_fields = ['name', 'ingredients']
    for field in required_fields:
        if field not in data or not data[field]:
            return f"Missing or empty required field: {field}"
    return None

@recipes_routes.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    try:
        data = request.get_json()
        logger.debug(f"PUT /api/recipes/{recipe_id}: Received data: {data}")

        # Validate the payload
        validation_error = validate_recipe_payload(data)
        if validation_error:
            logger.error(validation_error)
            return jsonify({'error': validation_error}), 400

        # Fetch the recipe by ID
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            logger.error(f"Recipe with ID {recipe_id} not found.")
            return jsonify({'error': f'Recipe with ID {recipe_id} not found.'}), 404

        # Update recipe fields
        recipe.name = data['name']
        recipe.cook_time = int(data['cook_time']) if data['cook_time'] else None
        recipe.servings = int(data['servings']) if data['servings'] else None
        recipe.instructions = data['instructions']

        # Process ingredients
        updated_ingredient_ids = []
        for ingredient_data in data['ingredients']:
            logger.debug(f"Processing ingredient data: {ingredient_data}")
            ingredient_id = ingredient_data.get('id')
            if ingredient_id:
                logger.debug(f"Existing ingredient ID: {ingredient_id}")
                recipe_ingredient = RecipeIngredient.query.get(ingredient_id)
            if recipe_ingredient:
                recipe_ingredient.quantity = float(Fraction(ingredient_data['quantity'])) if ingredient_data['quantity'] else None
                recipe_ingredient.unit = ingredient_data.get('unit', '') or None
                recipe_ingredient.size = ingredient_data.get('size', '') or None
                recipe_ingredient.descriptor = ingredient_data.get('descriptor', '') or None
                recipe_ingredient.additional_descriptor = ingredient_data.get('additional_descriptor', '') or None

                # Ensure ingredient name is correctly updated
                ingredient_obj = Ingredient.query.get(recipe_ingredient.ingredient_id)
                if ingredient_obj:
                    ingredient_obj.name = ingredient_data.get('item_name', '')

                db.session.commit()



                recipe_ingredient.size = ingredient_data.get('size', '')
                recipe_ingredient.descriptor = ingredient_data.get('descriptor', '')
                recipe_ingredient.additional_descriptor = ingredient_data.get('additional_descriptor', '')
                updated_ingredient_ids.append(recipe_ingredient.id)

            else:
                logger.debug("New ingredient, no ID provided.")
                # Ensure the ingredient exists
                ingredient_name = ingredient_data['item_name']
                existing_ingredient = Ingredient.query.filter_by(name=ingredient_name).first()

                if not existing_ingredient:
                    existing_ingredient = Ingredient(name=ingredient_name)
                    db.session.add(existing_ingredient)
                    db.session.flush()  # Ensure ingredient ID is available

                # ✅ Now, properly link the ingredient to the recipe using RecipeIngredient
                recipe_ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=existing_ingredient.id,
                    quantity=float(Fraction(ingredient_data['quantity'])) if ingredient_data['quantity'] else None,
                    unit=ingredient_data.get('unit', '')
                )
                db.session.add(recipe_ingredient)

                db.session.flush()
                updated_ingredient_ids.append(recipe_ingredient.id)

        # Remove ingredients not in the update
        RecipeIngredient.query.filter(
            RecipeIngredient.recipe_id == recipe.id,
            ~RecipeIngredient.id.in_(updated_ingredient_ids)
        ).delete(synchronize_session=False)


        # Commit changes
        db.session.commit()
        logger.info(f"Recipe updated successfully: {recipe}")
        return jsonify({
            **recipe.to_dict(),
            'ingredients': [ingredient.to_dict() for ingredient in recipe.ingredients]
        }), 200

    except Exception as e:
        import traceback
        logger.error(f"Error updating recipe: {str(e)}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@recipes_routes.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        db.session.delete(recipe)
        db.session.commit()
        return jsonify({'message': 'Recipe deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@recipes_routes.route('/', methods=['GET'])
def home():
    import os
    print(f"Template path: {os.path.join(current_app.template_folder, 'index.html')}")
    print(f"Static CSS path: {os.path.join(current_app.static_folder, 'css/styles.css')}")
    return render_template('index.html')

@meal_planner_routes.route('/api/weekly_plan', methods=['POST'])
def save_weekly_plan():
    """Save a new weekly meal plan."""
    try:
        # Parse request data
        data = request.json
        name = data.get('name', f"My Weekly Plan ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        meals = data.get('meals', [])

        if not meals:
            return jsonify({"error": "No meals provided"}), 400

        # Create and save the weekly plan
        weekly_plan = WeeklyPlan(name=name, created_at=datetime.utcnow())
        db.session.add(weekly_plan)

        # Flush to assign an ID to the weekly_plan
        db.session.flush()

        # Associate meals with the weekly plan
        for meal in meals:
            meal_slot = MealSlot(
                weekly_plan_id=weekly_plan.id,  # Now `weekly_plan.id` is available
                day=meal['day'],
                meal_type=meal['meal_type'],
                recipe_id=meal.get('recipe_id')
            )
            db.session.add(meal_slot)

        # Commit all changes to the database
        db.session.commit()

        return jsonify({"message": "Weekly plan saved successfully", "id": weekly_plan.id}), 201

    except Exception as e:
        logger.error(f"Error saving weekly plan: {e}")
        return jsonify({"error": "An error occurred while saving the plan"}), 500



def normalize_unit(unit):
    """Normalize units based on unit categories."""
    unit_mappings = {
        "unitless": "unitless",
        "Weight/Mass": {
            "Ounce (oz)": "Ounce (oz)",
            "Pound (lb)": "Pound (lb)",
            "Gram (g)": "Gram (g)",
            "Kilogram (kg)": "Kilogram (kg)",
            "Milligram (mg)": "Milligram (mg)"
        },
        "Volume": {
            "Tablespoon (tbsp)": "Tablespoon (tbsp)",
            "Teaspoon (tsp)": "Teaspoon (tsp)",
            "Cup": "Cup",
            "Liter (l)": "Liter (l)",
            "Milliliter (ml)": "Milliliter (ml)"
        },
        "Count/Units": {
            "Piece": "Piece",
            "Dozen": "Dozen"
        },
        "Miscellaneous/Traditional": {
            "Sprig": "Sprig",
            "Block": "Block",
            "Dash": "Dash",
            "Pinch": "Pinch",
            "Drop": "Drop",
            "Smidgen": "Smidgen",
            "Juice of": "Juice of",
            "Zest of": "Zest of"
        },
        "Specialty Units": {
            "Stick": "Stick",
            "Can": "Can",
            "Packet": "Packet"
        },
    }

    # Flatten the nested dictionary for quick lookup
    flat_mappings = {}
    for category, items in unit_mappings.items():
        if isinstance(items, dict):
            flat_mappings.update(items)
        else:
            flat_mappings[category] = items

    # Normalize the unit
    normalized = flat_mappings.get(unit)
    if normalized:
        return normalized
    else:
        # Log and return as-is if the unit is unknown
        logging.error(f"Unknown unit: {unit}")
        return unit




@meal_planner_routes.route('/api/weekly_plan_list', methods=['GET'])
def list_weekly_plans():
    """List all weekly plans."""
    try:
        plans = WeeklyPlan.query.all()
        return jsonify([{"id": plan.id, "name": plan.name} for plan in plans]), 200
    except Exception as e:
        logger.error(f"Error fetching weekly plans: {e}")
        return jsonify({"error": "An error occurred while fetching weekly plans."}), 500

@meal_planner_routes.route('/api/generate_grocery_list', methods=['POST'])
def save_and_generate_grocery_list():
    """Generate the grocery list without saving the plan automatically."""
    try:
        logger.debug(f"Raw request data: {request.data}")
        # Extract data from the request
        data = request.json
        if not data:
            raise ValueError("No data provided")
        logger.debug(f"Parsed JSON data: {data}")

        meals = data.get('meals', [])
        if not meals:
            logger.warning("No meals provided in the request.")
            return jsonify({"error": "No meals provided"}), 400

        # Collect ingredients from recipes including sub-recipes
        all_ingredients = []
        for meal in meals:
            recipe_id = meal.get('recipe_id')
            if recipe_id:
                ingredients = get_recipe_ingredients(recipe_id)
                all_ingredients.extend(ingredients)

        # Consolidate ingredients by name and unit
        consolidated = {}
        for ingredient in all_ingredients:
            key = (ingredient['item_name'], ingredient['unit'])
            if key not in consolidated:
                consolidated[key] = ingredient.copy()
            else:
                consolidated[key]['quantity'] += ingredient['quantity']
                # Update precision text
                consolidated[key]['precision_text'] = f"({consolidated[key]['quantity']} {consolidated[key]['unit']})"

        # Convert back to list and map to sections
        ingredients_list = list(consolidated.values())
        grocery_list = map_ingredients_to_sections(ingredients_list)
        logger.info(f"Generated categorized grocery list: {grocery_list}")

        return jsonify({"grocery_list": grocery_list})

    except Exception as e:
        logger.error(f"Error generating grocery list: {e}")
        return jsonify({"error": str(e)}), 500

@store_routes.route('/api/stores', methods=['POST'])
def create_or_update_store():
    data = request.json
    store_id = data.get('id')
    name = data.get('name')
    sections = data.get('sections', [])

    if store_id:
        store = Store.query.get(store_id)
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        store.name = name
    else:
        store = Store(name=name)
        db.session.add(store)

    db.session.flush()  # Get the store ID for new stores

    # Update sections
    existing_section_ids = {s.id for s in store.sections}
    incoming_section_ids = {s['id'] for s in sections if 'id' in s}

    # Delete removed sections
    Section.query.filter(Section.id.in_(existing_section_ids - incoming_section_ids)).delete()

    # Add or update sections
    for idx, section_data in enumerate(sections):
        if 'id' in section_data:
            section = Section.query.get(section_data['id'])
            section.name = section_data['name']
            section.order = idx
        else:
            new_section = Section(name=section_data['name'], order=idx, store_id=store.id)
            db.session.add(new_section)

    db.session.commit()
    return jsonify({'message': 'Store saved successfully', 'store_id': store.id})

@store_routes.route('/api/stores/<int:store_id>', methods=['DELETE'])
def delete_store(store_id):
    store = Store.query.get_or_404(store_id)
    db.session.delete(store)
    db.session.commit()
    return jsonify({'message': 'Store deleted successfully'})

@grocery_routes.route('/api/grocery_list', methods=['GET'])
def get_categorized_grocery_list():
    try:
        weekly_plan_id = request.args.get('weekly_plan_id')

        if not weekly_plan_id:
            return jsonify({'error': 'Weekly plan ID is required'}), 400

        weekly_plan = WeeklyPlan.query.get(weekly_plan_id)
        logger.debug(f"Weekly Plan found: {weekly_plan}")
        if not weekly_plan:
            return jsonify({'error': 'Weekly plan not found'}), 404

        # Assuming default store if no store ID provided
        store_id = request.args.get('store_id')
        store = Store.query.get(store_id) if store_id else Store.query.filter_by(is_default=True).first()

        if not store:
            return jsonify({'error': 'Store not found'}), 404

        sections = Section.query.filter_by(store_id=store.id).order_by(Section.order).all()
        logger.debug(f"Store used for sections: {store.name}")
        categorized_list = []

        for section in sections:
            logger.debug(f"Processing section: {section.name}")
            items = IngredientSection.query.filter_by(section_id=section.id).all()
            logger.debug(f"Items in section {section.name}: {[item.ingredient.item_name for item in items if item.ingredient]}")
            categorized_list.append({
                'section': section.name,
                'items': [
                    {
                        'name': item.ingredient.item_name,
                        'quantity': item.ingredient.quantity,
                        'unit': item.ingredient.unit
                    } for item in items if item.ingredient
                ]
            })
        logger.debug(f"Response being returned: {categorized_list}")
        return jsonify({'grocery_list': categorized_list})

    except Exception as e:
        logger.error(f"Error generating grocery list: {e}")
        return jsonify({"error": "An error occurred while generating the grocery list"}), 500


@ingredient_routes.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    # Example logic
    ingredients = Ingredient.query.all()
    return jsonify([ingredient.to_dict() for ingredient in ingredients])

@store_routes.route('/api/stores', methods=['GET'])
def get_stores():
    stores = Store.query.all()
    return jsonify([store.to_dict() for store in stores])

@grocery_routes.route('/grocery_list', methods=['GET'])
def grocery_list():
    """Render the grocery list HTML page."""
    try:
        weekly_plan_id = request.args.get('weekly_plan_id')
        logger.info(f"Rendering grocery_list.html for weekly_plan_id: {weekly_plan_id}")

        weekly_plan = WeeklyPlan.query.get(weekly_plan_id) if weekly_plan_id else None

        # Fetch past lists for display
        past_lists = WeeklyPlan.query.order_by(WeeklyPlan.created_at.desc()).all()

        return render_template(
            'grocery_list.html',
            weekly_plan=weekly_plan,
            ingredients=[],  # The frontend will fetch this via API
            past_lists=past_lists
        )
    except Exception as e:
        logger.error(f"Error rendering grocery list page: {e}")
        return "An error occurred while rendering the page", 500

def get_recipe_ingredients(recipe_id, quantity_multiplier=1.0, visited=None):
    """Recursively get all ingredients for a recipe, including from sub-recipes.
    
    Args:
        recipe_id: The ID of the recipe to get ingredients for
        quantity_multiplier: A multiplier to apply to ingredient quantities (for sub-recipes)
        visited: Set of already visited recipe IDs to prevent infinite loops
    
    Returns:
        List of ingredient dictionaries
    """
    if visited is None:
        visited = set()
    
    # Prevent circular references
    if recipe_id in visited:
        return []
    
    visited.add(recipe_id)
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return []
    
    result = []
    
    # Add direct ingredients
    for ingredient in recipe.ingredients:
        if ingredient.ingredient:  # Regular ingredient
            result.append({
                "id": ingredient.ingredient.id,
                "item_name": ingredient.ingredient.name,
                "quantity": (ingredient.quantity or 0) * quantity_multiplier,
                "unit": ingredient.unit or "",
                "main_text": ingredient.ingredient.name,
                "precision_text": f"({(ingredient.quantity or 0) * quantity_multiplier} {ingredient.unit or ''})"
            })
    
    # Add ingredients from sub-recipes
    for component in recipe.components:
        if component.sub_recipe_id:
            sub_quantity = component.quantity or 1.0
            sub_ingredients = get_recipe_ingredients(
                component.sub_recipe_id, 
                quantity_multiplier * sub_quantity,
                visited.copy()  # Pass a copy to avoid modifying the original
            )
            result.extend(sub_ingredients)
    
    return result

@meal_planner_routes.route('/api/grocery_list', methods=['GET'])
def get_grocery_list_json():
    """Return the grocery list as JSON."""
    try:
        weekly_plan_id = request.args.get('weekly_plan_id')
        logger.info(f"Received request for /api/grocery_list with weekly_plan_id: {weekly_plan_id}")
        if not weekly_plan_id:
            return jsonify({"error": "Weekly plan ID is required"}), 400

        weekly_plan = WeeklyPlan.query.get(weekly_plan_id)
        if not weekly_plan:
            logger.warning(f"Weekly plan not found for ID: {weekly_plan_id}")
            return jsonify({"error": "Weekly plan not found"}), 404
        
        logger.info(f"Weekly plan found: {weekly_plan.name}")

        # Gather ingredients
        ingredients = {}
        for meal in weekly_plan.meals:
            if meal.recipe_id:
                recipe = Recipe.query.get(meal.recipe_id)
                if recipe:
                    logger.info(f"Processing recipe: {recipe.name}")
                    for ingredient in recipe.ingredients:
                        key = (ingredient.item_name, ingredient.unit or "unitless")
                        ingredients[key] = ingredients.get(key, 0) + (ingredient.quantity or 0)

        logger.info(f"Collected ingredients: {ingredients}")

        # Format ingredients
        formatted_ingredients = [
            {"item_name": name, "unit": unit, "quantity": round(quantity, 2)}
            for (name, unit), quantity in ingredients.items()
        ]

        logger.info(f"Formatted ingredients: {formatted_ingredients}")

        return jsonify(formatted_ingredients)
    except Exception as e:
        logger.error(f"Error generating grocery list: {e}")
        return jsonify({"error": "An error occurred while generating the grocery list"}), 500

def map_ingredients_to_sections(ingredients):
    """Maps ingredients to store sections using SQLite instead of hardcoded values."""
    sections = {section.id: section.name for section in Section.query.all()}
    section_dict = {name: [] for name in sections.values()}

    for ingredient in ingredients:
        ingredient_id = ingredient["id"]

        # Fetch section from database
        ingredient_section = IngredientSection.query.filter_by(ingredient_id=ingredient_id).first()

        if ingredient_section:
            section_name = sections.get(ingredient_section.section_id, "Uncategorized")
        else:
            section_name = "Uncategorized"

        section_dict.setdefault(section_name, []).append({
            "main_text": ingredient["main_text"],
            "precision_text": ingredient["precision_text"],
        })

    return [{"section": name, "items": items} for name, items in section_dict.items()]





@ingredient_routes.route('/api/ingredients/<int:ingredient_id>/assign_section', methods=['POST'])
def assign_section_to_ingredient(ingredient_id):
    """Assign a section to an ingredient."""
    try:
        data = request.json
        if not data or 'section_id' not in data:
            return jsonify({"error": "Section ID is required"}), 400

        section_id = data['section_id']
        section = Section.query.get(section_id)
        if not section:
            return jsonify({"error": "Section not found"}), 404

        ingredient_section = IngredientSection.query.filter_by(ingredient_id=ingredient_id).first()
        if not ingredient_section:
            # Create a new mapping if none exists
            ingredient_section = IngredientSection(ingredient_id=ingredient_id, section_id=section_id)
            db.session.add(ingredient_section)
        else:
            # Update the existing mapping
            ingredient_section.section_id = section_id

        db.session.commit()
        return jsonify({"message": "Section assigned successfully", "ingredient_id": ingredient_id, "section_id": section_id})

    except Exception as e:
        logger.error(f"Error assigning section: {e}")
        return jsonify({"error": str(e)}), 500

@sub_recipes_bp.route('/<int:recipe_id>', methods=['GET'])
def get_sub_recipes(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return jsonify([component.to_dict() for component in recipe.components])

@sub_recipes_bp.route('/<int:recipe_id>', methods=['POST'])
def add_sub_recipe(recipe_id):
    data = request.json
    print(f"Received Data: {data}")  # Debugging Line
    
    sub_recipe_id = data.get('sub_recipe_id')
    quantity = data.get('quantity', 1)

    if not sub_recipe_id:
        return jsonify({'error': 'sub_recipe_id is required'}), 400

    parent_recipe = Recipe.query.get_or_404(recipe_id)
    sub_recipe = Recipe.query.get_or_404(sub_recipe_id)

    new_component = RecipeComponent(
    recipe_id=recipe_id,  # ✅ Use correct field name
    sub_recipe_id=sub_recipe_id,
    quantity=quantity
)



    db.session.add(new_component)
    db.session.commit()
    return jsonify(new_component.to_dict()), 201

@recipes_routes.route('/api/recipes/<int:recipe_id>/<int:sub_recipe_id>', methods=['DELETE'])
def remove_sub_recipe(recipe_id, sub_recipe_id):
    component = RecipeComponent.query.filter_by(
        recipe_id=recipe_id, sub_recipe_id=sub_recipe_id
    ).first_or_404()

    db.session.delete(component)
    db.session.commit()

    return jsonify({'message': 'Sub-recipe link removed successfully'}), 200



@recipes_routes.route('/api/recipes', methods=['GET'])
def search_recipes():
    query = request.args.get('search', '')
    
    if query:
        recipes = Recipe.query.filter(Recipe.name.ilike(f"%{query}%")).all()
    else:
        recipes = Recipe.query.all()

    return jsonify([recipe.to_dict() for recipe in recipes])

# Add/modify these routes in routes.py (around line 502, after the existing sub-recipe endpoints)

@sub_recipes_bp.route('/', methods=['GET'])
def list_all_sub_recipes():
    """Get all recipes suitable for use as sub-recipes"""
    recipes = Recipe.query.all()
    return jsonify([{
        'id': recipe.id,
        'name': recipe.name,
        'used_as_sub': len(recipe.used_in_recipes) > 0
    } for recipe in recipes])

@sub_recipes_bp.route('/recipe/<int:recipe_id>/components', methods=['GET'])
def get_recipe_components(recipe_id):
    """Get all sub-recipes used in a specific recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Get components with sub_recipe details
    components = [{
        'id': component.id,
        'quantity': component.quantity,
        'sub_recipe': {
            'id': component.sub_recipe.id,
            'name': component.sub_recipe.name,
        }
    } for component in recipe.components]
    
    return jsonify(components)

@sub_recipes_bp.route('/check_circular', methods=['POST'])
def check_circular_reference():
    """Check if adding a sub-recipe would create a circular reference"""
    data = request.json
    parent_id = data.get('parent_id')
    sub_recipe_id = data.get('sub_recipe_id')
    
    if parent_id == sub_recipe_id:
        return jsonify({'circular': True, 'message': 'Cannot add a recipe as its own sub-recipe'})
    
    # Check if sub_recipe contains parent recursively
    def check_recursive(recipe_id, target_id, visited=None):
        if visited is None:
            visited = set()
        
        if recipe_id in visited:
            return False
        
        visited.add(recipe_id)
        
        components = RecipeComponent.query.filter_by(recipe_id=recipe_id).all()
        for component in components:
            if component.sub_recipe_id == target_id:
                return True
            if check_recursive(component.sub_recipe_id, target_id, visited):
                return True
        
        return False
    
    is_circular = check_recursive(sub_recipe_id, parent_id)
    
    return jsonify({
        'circular': is_circular,
        'message': 'Adding this sub-recipe would create a circular reference' if is_circular else 'No circular reference detected'
    })
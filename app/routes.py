from fractions import Fraction
import logging
from flask import Blueprint, jsonify, request, render_template, current_app
from app.utils import parse_ingredients  # Importing the missing function
from app import db
from app.utils import convert_to_base_unit
from datetime import datetime
from app.models import Store, Section, IngredientSection, Ingredient, Recipe, WeeklyPlan, MealSlot
from collections import defaultdict


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

def format_grocery_list_with_default_sections(ingredients):
    from collections import defaultdict  # Ensure you have the import
    grouped = defaultdict(list)
    for item in ingredients:
        section = item.get('section', 'Uncategorized') or 'Uncategorized'
        grouped[section].append(item)

    for section in DEFAULT_SECTIONS:
        if section not in grouped:
            grouped[section] = []

    return [{"section": section, "items": grouped[section]} for section in grouped]

@recipes_routes.route('/recipes', methods=['GET'])
def recipes():
    return render_template('recipes.html')

@recipes_routes.route('/api/recipes', methods=['GET'])
def get_recipes():
    try:
        recipes = Recipe.query.all()
        # Serialize each recipe and its ingredients
        return jsonify([{
            **recipe.to_dict(),
            'ingredients': [ingredient.to_dict() for ingredient in recipe.ingredients]
        } for recipe in recipes])
    except Exception as e:
        logger.error(f"Error fetching recipes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@recipes_routes.route('/api/recipes', methods=['POST'])
def add_recipe():
    try:
        data = request.get_json()
        logger.debug(f"Received data: {data}")

        # Check if this is an existing recipe
        recipe_id = data.get('id')
        if recipe_id:
            new_recipe = Recipe.query.get(recipe_id)
            if not new_recipe:
                return jsonify({'error': 'Recipe not found'}), 404
        else:
            # Create a new recipe
            new_recipe = Recipe(
                name=data['name'],
                cook_time=int(data['cook_time']) if data['cook_time'] else None,
                servings=int(data['servings']) if data['servings'] else None,
                instructions=data['instructions']
            )
            db.session.add(new_recipe)

        # Update recipe fields
        new_recipe.name = data['name']
        new_recipe.cook_time = int(data['cook_time']) if data['cook_time'] else None
        new_recipe.servings = int(data['servings']) if data['servings'] else None
        new_recipe.instructions = data['instructions']

        # Handle ingredients
        if 'ingredients' in data and data['ingredients']:
            # Track ingredient IDs that were updated or added
            updated_ingredient_ids = []

            for ingredient_data in data['ingredients']:
                ingredient_id = ingredient_data.get('id')
                if ingredient_id:
                    # Update existing ingredient
                    ingredient = Ingredient.query.get(ingredient_id)
                    if ingredient:
                        ingredient.item_name = ingredient_data['item_name']
                        ingredient.quantity = float(Fraction(ingredient_data['quantity'])) if ingredient_data['quantity'] else None
                        ingredient.original_quantity = ingredient_data.get('quantity', '')
                        ingredient.unit = ingredient_data.get('unit', '')
                        ingredient.size = ingredient_data.get('size', '')
                        ingredient.descriptor = ingredient_data.get('descriptor', '')
                        ingredient.additional_descriptor = ingredient_data.get('additional_descriptor', '')
                        updated_ingredient_ids.append(ingredient.id)
                else:
                    # Add new ingredient
                    ingredient = Ingredient(
                        recipe=new_recipe,
                        item_name=ingredient_data['item_name'],
                        quantity=float(Fraction(ingredient_data['quantity'])) if ingredient_data['quantity'] else None,
                        original_quantity=ingredient_data.get('quantity', ''),
                        unit=ingredient_data.get('unit', ''),
                        size=ingredient_data.get('size', ''),
                        descriptor=ingredient_data.get('descriptor', ''),
                        additional_descriptor=ingredient_data.get('additional_descriptor', '')
                    )
                    db.session.add(ingredient)
                    db.session.flush()  # Ensure we get the ID of the new ingredient
                    updated_ingredient_ids.append(ingredient.id)

            # Remove ingredients that are no longer part of the recipe
            Ingredient.query.filter(
                Ingredient.recipe_id == new_recipe.id,
                ~Ingredient.id.in_(updated_ingredient_ids)
            ).delete(synchronize_session=False)

        # Commit changes
        db.session.commit()
        logger.info(f"Recipe saved successfully: {new_recipe}")
        return jsonify({
            **new_recipe.to_dict(),
            'ingredients': [ingredient.to_dict() for ingredient in new_recipe.ingredients]
        }), 201

    except Exception as e:
        logger.error(f"Error saving recipe: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500




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
                ingredient = Ingredient.query.get(ingredient_id)
                if ingredient:
                    ingredient.item_name = ingredient_data['item_name']
                    ingredient.quantity = float(Fraction(ingredient_data['quantity'])) if ingredient_data['quantity'] else None
                    ingredient.original_quantity = ingredient_data.get('quantity', '')
                    ingredient.unit = ingredient_data.get('unit', '')
                    ingredient.size = ingredient_data.get('size', '')
                    ingredient.descriptor = ingredient_data.get('descriptor', '')
                    ingredient.additional_descriptor = ingredient_data.get('additional_descriptor', '')
                    updated_ingredient_ids.append(ingredient.id)
            else:
                logger.debug("New ingredient, no ID provided.")
                ingredient = Ingredient(
                    recipe=recipe,
                    item_name=ingredient_data['item_name'],
                    quantity=float(Fraction(ingredient_data['quantity'])) if ingredient_data['quantity'] else None,
                    original_quantity=ingredient_data.get('quantity', ''),
                    unit=ingredient_data.get('unit', ''),
                    size=ingredient_data.get('size', ''),
                    descriptor=ingredient_data.get('descriptor', ''),
                    additional_descriptor=ingredient_data.get('additional_descriptor', '')
                )
                db.session.add(ingredient)
                db.session.flush()
                updated_ingredient_ids.append(ingredient.id)

        # Remove ingredients not in the update
        Ingredient.query.filter(
            Ingredient.recipe_id == recipe.id,
            ~Ingredient.id.in_(updated_ingredient_ids)
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



@recipes_routes.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        return jsonify(recipe.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        # Extract data from the request
        data = request.json
        logger.debug(f"Received data: {data}")

        # Validate required fields
        meals = data.get('meals', [])
        if not meals:
            logger.warning("No meals provided in the request.")
            return jsonify({"error": "No meals provided"}), 400

        # Generate the grocery list (without saving a weekly plan)
        ingredients = {}
        for meal in meals:
            recipe_id = meal.get('recipe_id')
            if recipe_id:
                recipe = Recipe.query.get(recipe_id)
                if recipe:
                    logger.debug(f"Processing recipe: {recipe.name}")
                    for ingredient in recipe.ingredients:
                        if not ingredient.item_name or ingredient.quantity is None or not ingredient.unit:
                            logger.warning(f"Invalid ingredient data: {ingredient.to_dict()}")
                            continue
                        key = (ingredient.item_name, ingredient.unit or "unitless")
                        ingredients[key] = ingredients.get(key, 0) + (ingredient.quantity or 0)

        formatted_ingredients = [
            {"item_name": name, "unit": unit, "quantity": round(quantity, 2)}
            for (name, unit), quantity in ingredients.items()
        ]
        logger.info(f"Generated grocery list: {formatted_ingredients}")

        # Pass the generated list back for rendering
        return jsonify({"grocery_list": formatted_ingredients})

    except Exception as e:
        logger.error(f"Error generating grocery list: {e}", exc_info=True)
        return jsonify({"error": "An error occurred"}), 500


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

@ingredient_routes.route('/api/ingredients/<int:ingredient_id>/assign_section', methods=['POST'])
def assign_section_to_ingredient(ingredient_id):
    data = request.json
    section_id = data.get('section_id')

    # Assign section to ingredient
    mapping = IngredientSection.query.filter_by(ingredient_id=ingredient_id).first()
    if mapping:
        mapping.section_id = section_id
    else:
        mapping = IngredientSection(ingredient_id=ingredient_id, section_id=section_id)
        db.session.add(mapping)

    db.session.commit()
    return jsonify({'message': 'Ingredient assigned to section'})


@grocery_routes.route('/api/grocery_list', methods=['GET'])
def get_categorized_grocery_list():
    """Return the categorized grocery list."""
    try:
        weekly_plan_id = request.args.get('weekly_plan_id')
        logger.info(f"Received weekly_plan_id: {weekly_plan_id}")

        if not weekly_plan_id:
            return jsonify({'error': 'Weekly plan ID is required'}), 400

        # Fetch the weekly plan
        weekly_plan = WeeklyPlan.query.get(weekly_plan_id)
        logger.info(f"Weekly plan: {weekly_plan.name if weekly_plan else 'None'}")
        if not weekly_plan:
            logger.warning(f"Weekly plan not found for ID: {weekly_plan_id}")
            return jsonify({'error': 'Weekly plan not found'}), 404

        if not weekly_plan.meals:
            logger.warning(f"Weekly plan {weekly_plan_id} has no meals associated.")
            return jsonify({'error': 'No meals in this weekly plan'}), 400

        # Fetch the store
        store_id = request.args.get('store_id')
        store = Store.query.get(store_id) if store_id else Store.query.filter_by(is_default=True).first()
        logger.info(f"Store: {store.name if store else 'None'}")  # Add here
        if not store:
            logger.warning(f"No store found. Store ID: {store_id}")
            return jsonify({'error': 'Store not found'}), 404

        # Build the categorized list
        categorized_list = []
        for section in store.sections:
            items = IngredientSection.query.filter_by(section_id=section.id).all()
            categorized_list.append({
                'section': section.name,
                'items': [
                    {
                        'name': item.ingredient.item_name if item.ingredient else 'Unknown Ingredient',
                        'quantity': item.ingredient.quantity if item.ingredient else 0,
                        'unit': item.ingredient.unit if item.ingredient else 'unitless'
                    }
                    for item in items if item.ingredient  # Only include valid ingredients
                ]
            })

        # Add missing default sections
        for default_section in DEFAULT_SECTIONS:
            if not any(category['section'] == default_section for category in categorized_list):
                categorized_list.append({"section": default_section, "items": []})
            
            logger.info(f"Categorized grocery list: {categorized_list}")
            return jsonify(categorized_list)

    except Exception as e:
        logger.error(f"Error generating categorized grocery list: {e}")
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

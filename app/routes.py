from fractions import Fraction
import math
import re
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

# In routes.py
# Update the add_recipe function

@recipes_routes.route('/api/recipes', methods=['POST'])
def add_recipe():
    data = request.get_json()
    logger.debug(f"Recipe data received: {data}")

    # Create or update recipe
    recipe = Recipe.query.get(data.get('id')) if data.get('id') else Recipe()
    recipe.name = data['name']
    recipe.cook_time = data['cook_time'] if data['cook_time'] else None
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
            quantity_str = ingredient_data.get('quantity', '1')
            quantity_float, _, _, _ = parse_fraction(str(quantity_str))
            
            component = RecipeComponent(
                recipe_id=recipe.id,
                sub_recipe_id=sub_recipe_id,
                quantity=quantity_float or 1.0
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

            # Parse quantity as potential fraction
            quantity_str = ingredient_data.get('quantity', '')
            quantity_float, numerator, denominator, is_fraction = parse_fraction(str(quantity_str))

            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=quantity_float,
                unit=ingredient_data.get('unit', ''),
                size=ingredient_data.get('size', ''),
                descriptor=ingredient_data.get('descriptor', ''),
                additional_descriptor=ingredient_data.get('additional_descriptor', ''),
                is_fraction=is_fraction,
                quantity_numerator=numerator,
                quantity_denominator=denominator
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
        recipe.cook_time = data['cook_time'] if data['cook_time'] else None
        recipe.servings = int(data['servings']) if data['servings'] else None
        recipe.instructions = data['instructions']

        # Process ingredients - separate regular ingredients from sub-recipes
        regular_ingredients = []
        sub_recipes = []
        
        for item in data['ingredients']:
            if 'sub_recipe_id' in item and item['sub_recipe_id']:
                # This is a sub-recipe
                sub_recipes.append(item)
            else:
                # This is a regular ingredient
                regular_ingredients.append(item)
        
        logger.debug(f"Regular ingredients: {regular_ingredients}")
        logger.debug(f"Sub-recipes: {sub_recipes}")
        
        # Clear existing ingredients and components to rebuild them
        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
        RecipeComponent.query.filter_by(recipe_id=recipe.id).delete()
        
        # Re-add regular ingredients
        for ingredient_data in regular_ingredients:
            ingredient_name = ingredient_data.get('item_name')
            if not ingredient_name:
                continue  # Skip ingredients without a name
                
            # Find or create the ingredient
            ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
            if not ingredient:
                ingredient = Ingredient(name=ingredient_name)
                db.session.add(ingredient)
                db.session.flush()
            
            # Parse quantity as potential fraction
            quantity_str = ingredient_data.get('quantity', '')
            quantity_float, numerator, denominator, is_fraction = parse_fraction(str(quantity_str))
            
            # Create the recipe ingredient
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=quantity_float,
                unit=ingredient_data.get('unit', ''),
                size=ingredient_data.get('size', ''),
                descriptor=ingredient_data.get('descriptor', ''),
                additional_descriptor=ingredient_data.get('additional_descriptor', ''),
                is_fraction=is_fraction,
                quantity_numerator=numerator,
                quantity_denominator=denominator
            )
            db.session.add(recipe_ingredient)
        
        # Re-add sub-recipes as components
        for sub_recipe_data in sub_recipes:
            sub_recipe_id = sub_recipe_data.get('sub_recipe_id')
            if not sub_recipe_id:
                continue  # Skip invalid sub-recipes
            
            # Parse quantity as potential fraction for sub-recipes
            quantity_str = sub_recipe_data.get('quantity', '1')
            quantity_float, _, _, _ = parse_fraction(str(quantity_str))
                
            # Create the component
            component = RecipeComponent(
                recipe_id=recipe.id,
                sub_recipe_id=sub_recipe_id,
                quantity=quantity_float or 1.0
            )
            db.session.add(component)

        # Commit all changes
        db.session.commit()
        logger.info(f"Recipe updated successfully: {recipe}")
        
        # Return the updated recipe with all details
        return jsonify(recipe.to_dict()), 200

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

# In routes.py
# Update the get_categorized_grocery_list function
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

        # Get all ingredients from the weekly plan
        all_ingredients = []
        for meal in weekly_plan.meals:
            if meal.recipe_id:
                ingredients = get_recipe_ingredients(meal.recipe_id)
                all_ingredients.extend(ingredients)

        # Consolidate ingredients by name and unit
        ingredient_map = {}
        for ingredient in all_ingredients:
            key = (ingredient['item_name'], ingredient.get('unit', ''))
            if key not in ingredient_map:
                ingredient_map[key] = ingredient.copy()
            else:
                # Add quantities
                if ingredient.get('is_fraction') and ingredient_map[key].get('is_fraction'):
                    # Handle fractions
                    result = combine_quantities([
                        ingredient_map[key],
                        ingredient
                    ])
                    ingredient_map[key].update(result)
                else:
                    # Simple addition for regular quantities
                    ingredient_map[key]['quantity'] += ingredient.get('quantity', 0)

        # Convert back to list
        consolidated_ingredients = list(ingredient_map.values())

        # Get all sections
        sections = Section.query.order_by(Section.order).all()
        
        # Create the categorized grocery list
        categorized_list = []
        uncategorized_items = []
        
        # Check each ingredient and assign to appropriate section
        for ingredient in consolidated_ingredients:
            ingredient_id = ingredient.get('id')
            ingredient_name = ingredient.get('item_name')
            
            # Try to find the ingredient in the database
            db_ingredient = None
            if ingredient_id:
                db_ingredient = Ingredient.query.get(ingredient_id)
            
            if not db_ingredient and ingredient_name:
                db_ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
            
            # Find the section for this ingredient
            section = None
            if db_ingredient:
                ingredient_section = IngredientSection.query.filter_by(ingredient_id=db_ingredient.id).first()
                if ingredient_section:
                    section = ingredient_section.section
            
            # Format the ingredient display
            display_item = {
                'id': ingredient.get('id'),
                'name': ingredient.get('item_name'),
                'quantity': ingredient.get('quantity'),
                'unit': ingredient.get('unit', ''),
                'is_fraction': ingredient.get('is_fraction', False)
            }
            
            # Add fraction string if available
            if ingredient.get('is_fraction') and ingredient.get('quantity_numerator') and ingredient.get('quantity_denominator'):
                numerator = ingredient['quantity_numerator']
                denominator = ingredient['quantity_denominator']
                
                if numerator >= denominator:
                    whole_part = numerator // denominator
                    remainder = numerator % denominator
                    if remainder == 0:
                        display_item['fraction_str'] = str(whole_part)
                    else:
                        display_item['fraction_str'] = f"{whole_part} {remainder}/{denominator}"
                else:
                    display_item['fraction_str'] = f"{numerator}/{denominator}"
            
            # Add to appropriate section or uncategorized
            if section:
                # Find or create section in result
                section_entry = next(
                    (s for s in categorized_list if s['section'] == section.name),
                    None
                )
                
                if not section_entry:
                    section_entry = {'section': section.name, 'items': []}
                    categorized_list.append(section_entry)
                
                section_entry['items'].append(display_item)
            else:
                uncategorized_items.append(display_item)
        
        # Add uncategorized section at the end if needed
        if uncategorized_items:
            categorized_list.append({
                'section': 'Uncategorized',
                'items': uncategorized_items
            })
        
        # Sort sections by store order
        section_order = {section.name: section.order for section in sections}
        categorized_list.sort(key=lambda x: section_order.get(x['section'], float('inf')))
        
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

# In routes.py
# Update get_recipe_ingredients to include fraction data
def get_recipe_ingredients(recipe_id, quantity_multiplier=1.0, visited=None):
    """Recursively get all ingredients for a recipe, including from sub-recipes."""
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
            quantity_info = {
                'quantity': (ingredient.quantity or 0) * quantity_multiplier,
                'is_fraction': ingredient.is_fraction
            }
            
            # Handle fractions
            if ingredient.is_fraction and ingredient.quantity_numerator is not None and ingredient.quantity_denominator is not None:
                # Scale the fraction by the multiplier
                numerator = int(ingredient.quantity_numerator * quantity_multiplier)
                denominator = ingredient.quantity_denominator
                quantity_info['quantity_numerator'] = numerator
                quantity_info['quantity_denominator'] = denominator
                
                # Generate a display string for the fraction
                if numerator >= denominator:
                    whole_part = numerator // denominator
                    remainder = numerator % denominator
                    if remainder == 0:
                        fraction_display = str(whole_part)
                    else:
                        fraction_display = f"{whole_part} {remainder}/{denominator}"
                else:
                    fraction_display = f"{numerator}/{denominator}"
                    
                precision_text = f"({fraction_display} {ingredient.unit or ''})"
            else:
                # Handle regular decimal quantities
                precision_text = f"({(ingredient.quantity or 0) * quantity_multiplier} {ingredient.unit or ''})"
                
            result.append({
                "id": ingredient.ingredient.id,
                "item_name": ingredient.ingredient.name,
                "quantity": (ingredient.quantity or 0) * quantity_multiplier,
                "unit": ingredient.unit or "",
                "main_text": ingredient.ingredient.name,
                "precision_text": precision_text,
                "is_fraction": ingredient.is_fraction,
                "quantity_numerator": ingredient.quantity_numerator,
                "quantity_denominator": ingredient.quantity_denominator
            })
    
    # Add ingredients from sub-recipes
    for component in recipe.components:
        if component.sub_recipe_id:
            sub_quantity = component.quantity or 1.0
            sub_ingredients = get_recipe_ingredients(
                component.sub_recipe_id, 
                quantity_multiplier * sub_quantity,
                visited.copy()
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
        all_ingredients = []
        for meal in weekly_plan.meals:
            if meal.recipe_id:
                ingredients = get_recipe_ingredients(meal.recipe_id)
                all_ingredients.extend(ingredients)

        # Map ingredients to sections and format as expected by the frontend
        grocery_list = map_ingredients_to_sections(all_ingredients)
        
        # Return in the format expected by the frontend
        return jsonify({"grocery_list": grocery_list})
        
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

        # Update this part to match what the frontend expects
        section_dict.setdefault(section_name, []).append({
            "name": ingredient["main_text"],  # Change main_text to name
            "quantity": ingredient.get("quantity", 0),
            "unit": ingredient.get("unit", ""),
            "fraction_str": ingredient.get("fraction_str"),
            # Keep precision_text for backward compatibility
            "precision_text": ingredient.get("precision_text")
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

@meal_planner_routes.route('/api/weekly_plan/<int:plan_id>', methods=['GET'])
def get_weekly_plan(plan_id):
    """Get details for a specific weekly plan."""
    try:
        plan = WeeklyPlan.query.get_or_404(plan_id)
        
        # Get meal slots
        meal_slots = MealSlot.query.filter_by(weekly_plan_id=plan_id).all()
        
        # Calculate ingredient count safely
        try:
            ingredient_count = plan.ingredient_count
        except Exception as e:
            logger.error(f"Error calculating ingredient count: {e}")
            ingredient_count = 0
        
        return jsonify({
            'id': plan.id,
            'name': plan.name,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
            'meals': [meal.to_dict() for meal in meal_slots],
            'ingredient_count': ingredient_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching weekly plan {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500

@meal_planner_routes.route('/api/weekly_plan/<int:plan_id>', methods=['DELETE'])
def delete_weekly_plan(plan_id):
    """Delete a weekly plan."""
    try:
        plan = WeeklyPlan.query.get_or_404(plan_id)
        
        # Delete will cascade to meal slots due to relationship definition
        db.session.delete(plan)
        db.session.commit()
        
        return jsonify({"message": "Weekly plan deleted successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error deleting weekly plan {plan_id}: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@meal_planner_routes.route('/api/weekly_plan/<int:plan_id>/update', methods=['PUT'])
def update_weekly_plan(plan_id):
    """Update an existing weekly plan."""
    try:
        plan = WeeklyPlan.query.get_or_404(plan_id)
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Update plan name if provided
        if 'name' in data:
            plan.name = data['name']
            
        # Update meals if provided
        if 'meals' in data:
            # Delete existing meal slots
            MealSlot.query.filter_by(weekly_plan_id=plan_id).delete()
            
            # Add new meal slots
            for meal in data['meals']:
                meal_slot = MealSlot(
                    weekly_plan_id=plan_id,
                    day=meal['day'],
                    meal_type=meal['meal_type'],
                    recipe_id=meal.get('recipe_id')
                )
                db.session.add(meal_slot)
                
        # Update timestamp
        plan.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": "Weekly plan updated successfully",
            "id": plan.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating weekly plan {plan_id}: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def parse_fraction(fraction_str):
    """Parse a fraction string into numerator and denominator."""
    if not fraction_str or fraction_str.strip() == '':
        return None, None, None, False
        
    # Remove any extra whitespace
    fraction_str = str(fraction_str).strip()
    
    # Check if it's a simple number
    try:
        return float(fraction_str), None, None, False
    except ValueError:
        pass
        
    # Try to parse as fraction
    try:
        # Check for mixed number format like "1 1/2"
        mixed_match = re.match(r'(\d+)\s+(\d+)/(\d+)', fraction_str)
        if mixed_match:
            whole = int(mixed_match.group(1))
            numerator = int(mixed_match.group(2))
            denominator = int(mixed_match.group(3))
            # Convert to improper fraction
            numerator = whole * denominator + numerator
            return float(numerator) / float(denominator), numerator, denominator, True
            
        # Check for simple fraction like "1/2"
        fraction_match = re.match(r'(\d+)/(\d+)', fraction_str)
        if fraction_match:
            numerator = int(fraction_match.group(1))
            denominator = int(fraction_match.group(2))
            return float(numerator) / float(denominator), numerator, denominator, True
            
        # Convert string to Fraction object
        frac = Fraction(fraction_str)
        return float(frac), frac.numerator, frac.denominator, True
    except (ValueError, ZeroDivisionError):
        return None, None, None, False
    
def combine_quantities(quantities):
    """Combine a list of quantities, handling fractions properly."""
    total = 0
    numerator_sum = 0
    denominator = None
    has_fraction = False
    
    for qty in quantities:
        if isinstance(qty, dict):  # Handle dictionary format
            if qty.get('is_fraction') and qty.get('quantity_numerator') and qty.get('quantity_denominator'):
                has_fraction = True
                num = qty['quantity_numerator']
                den = qty['quantity_denominator']
                
                if denominator is None:
                    denominator = den
                    numerator_sum = num
                else:
                    # Convert to common denominator
                    lcm = (denominator * den) // math.gcd(denominator, den)
                    numerator_sum = (numerator_sum * (lcm // denominator)) + (num * (lcm // den))
                    denominator = lcm
            else:
                total += qty.get('quantity', 0)
        else:  # Handle numeric values
            total += qty
    
    if has_fraction:
        # Convert total to fraction with the same denominator
        if denominator:
            numerator_sum += int(total * denominator)
            # Simplify the fraction
            gcd = math.gcd(numerator_sum, denominator)
            return {
                'quantity': float(numerator_sum / denominator),
                'is_fraction': True,
                'quantity_numerator': numerator_sum // gcd,
                'quantity_denominator': denominator // gcd
            }
    
    return {'quantity': total, 'is_fraction': False}

# In routes.py
# Add a route to save ingredient-to-section mappings
@store_routes.route('/api/save_ingredient_sections', methods=['POST'])
def save_ingredient_sections():
    """Save ingredient-to-section mappings with custom ordering."""
    try:
        data = request.get_json()
        if not data or 'sections' not in data:
            return jsonify({"error": "No section data provided"}), 400
            
        # Clear existing mappings if specified
        if data.get('clear_existing', False):
            IngredientSection.query.delete()
            
        # Process each section and its ingredients
        for section_data in data['sections']:
            section_id = section_data.get('id')
            section_name = section_data.get('name')
            ingredients = section_data.get('ingredients', [])
            
            # Get or create the section
            section = None
            if section_id:
                section = Section.query.get(section_id)
            
            if not section and section_name:
                # Check if section exists by name
                section = Section.query.filter_by(name=section_name).first()
                
                if not section:
                    # Create new section
                    store_id = data.get('store_id', 1)  # Default to store ID 1 if not specified
                    section_order = Section.query.filter_by(store_id=store_id).count()
                    section = Section(name=section_name, order=section_order, store_id=store_id)
                    db.session.add(section)
                    db.session.flush()
            
            if not section:
                continue
                
            # Process ingredients for this section
            for i, ingredient_data in enumerate(ingredients):
                ingredient_id = ingredient_data.get('id')
                ingredient_name = ingredient_data.get('name')
                
                # Get or create the ingredient
                ingredient = None
                if ingredient_id:
                    ingredient = Ingredient.query.get(ingredient_id)
                
                if not ingredient and ingredient_name:
                    ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
                    
                    if not ingredient:
                        ingredient = Ingredient(name=ingredient_name)
                        db.session.add(ingredient)
                        db.session.flush()
                
                if not ingredient:
                    continue
                    
                # Check if mapping already exists
                mapping = IngredientSection.query.filter_by(
                    ingredient_id=ingredient.id,
                    section_id=section.id
                ).first()
                
                if mapping:
                    # Update existing mapping
                    mapping.order = i
                else:
                    # Create new mapping
                    mapping = IngredientSection(
                        ingredient_id=ingredient.id,
                        section_id=section.id,
                        order=i
                    )
                    db.session.add(mapping)
        
        db.session.commit()
        return jsonify({"message": "Ingredient sections saved successfully"})
        
    except Exception as e:
        logger.error(f"Error saving ingredient sections: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
    # In routes.py
# Add this route to get ingredient sections by store
@store_routes.route('/api/ingredient_sections', methods=['GET'])
def get_ingredient_sections():
    """Get all ingredient-to-section mappings for a store."""
    try:
        store_id = request.args.get('store_id')
        if not store_id:
            return jsonify({"error": "Store ID is required"}), 400
            
        # Get sections for this store
        sections = Section.query.filter_by(store_id=store_id).all()
        section_ids = [section.id for section in sections]
        
        # Get ingredient mappings for these sections
        mappings = IngredientSection.query.filter(IngredientSection.section_id.in_(section_ids)).all()
        
        result = [{
            'id': mapping.id,
            'ingredient_id': mapping.ingredient_id,
            'section_id': mapping.section_id,
            'order': mapping.order
        } for mapping in mappings]
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting ingredient sections: {e}")
        return jsonify({"error": str(e)}), 500
    
    # In routes.py
# Add this route to get sections for a store
@store_routes.route('/api/stores/<int:store_id>/sections', methods=['GET'])
def get_store_sections(store_id):
    """Get all sections for a specific store."""
    try:
        sections = Section.query.filter_by(store_id=store_id).order_by(Section.order).all()
        
        result = [{
            'id': section.id,
            'name': section.name,
            'order': section.order
        } for section in sections]
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting store sections: {e}")
        return jsonify({"error": str(e)}), 500
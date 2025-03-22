from flask import Blueprint, jsonify, request
from app import db
from app.models import (
    WeeklyPlan, MealSlot, Recipe, RecipeIngredient, 
    Ingredient, Section, IngredientSection, Store
)
from app.utils.grocery_list_aggregation import aggregate_grocery_list, format_for_display
from app.utils.utils import get_recipe_ingredients, format_ingredient_for_display, deduplicate_sections, map_ingredients_to_sections
from app.utils.ingredient_aggregator import aggregate_ingredients_with_units
from .meal_planner import meal_planner_routes
import logging
from flask_cors import CORS

grocery_routes = Blueprint('grocery_routes', __name__)
CORS(grocery_routes)  # Enable CORS for this blueprint

generate_grocery_bp = Blueprint('generate_grocery', __name__)
CORS(generate_grocery_bp) 

# Configure logging
logger = logging.getLogger(__name__)


@grocery_routes.route('/api/grocery_list', methods=['GET'])
def get_categorized_grocery_list():
    try:
        weekly_plan_id = request.args.get('weekly_plan_id')
        store_id = request.args.get('store_id')

        if not weekly_plan_id:
            return jsonify({'error': 'Weekly plan ID is required'}), 400

        # Get all ingredients from the weekly plan
        all_ingredients = []
        weekly_plan = WeeklyPlan.query.get(weekly_plan_id)
        
        if not weekly_plan:
            return jsonify({'error': 'Weekly plan not found'}), 404
            
        for meal in weekly_plan.meals:
            if meal.recipe_id:
                # get_recipe_ingredients will automatically filter out sub-recipes
                ingredients = get_recipe_ingredients(meal.recipe_id)
                all_ingredients.extend(ingredients)

        ingredient_map = {}
        for ingredient in all_ingredients:
            key = (ingredient['item_name'], ingredient.get('unit', ''))
            if key not in ingredient_map:
                ingredient_map[key] = ingredient.copy()
            else:
                # Handle addition logic...
                if 'quantity' in ingredient and 'quantity' in ingredient_map[key]:
                    ingredient_map[key]['quantity'] += ingredient['quantity']
        
        consolidated_ingredients = list(ingredient_map.values())
        logger.debug(f"Consolidated {len(all_ingredients)} ingredients into {len(consolidated_ingredients)} unique items")
        
        # Get all section mappings
        if store_id:
            # Get all ingredient-section mappings for this store at once
            mappings = IngredientSection.query.join(Section).filter(Section.store_id == store_id).all()
            ingredients_to_sections = {mapping.ingredient_id: mapping.section_id for mapping in mappings}
            
            logger.debug(f"Found {len(mappings)} ingredient-section mappings")
                
            # Get all sections for this store
            sections = Section.query.filter_by(store_id=store_id).order_by(Section.order).all()
            section_dict = {section.id: {'name': section.name, 'order': section.order, 'items': []} for section in sections}
            
            # Add uncategorized bucket
            section_dict['uncategorized'] = {'name': 'Uncategorized', 'order': 999, 'items': []}
            
            # Assign ingredients to sections
            for ingredient in consolidated_ingredients:
                ingredient_id = ingredient.get('id')
                ingredient_name = ingredient.get('item_name', '').lower()
                ingredient_obj = None
                
                # Find the ingredient in the database if we have an ID
                if ingredient_id:
                    ingredient_obj = Ingredient.query.get(ingredient_id)
                
                # If no ID or not found by ID, try finding by name
                if not ingredient_obj and ingredient_name:
                    ingredient_obj = Ingredient.query.filter(Ingredient.name.ilike(f"%{ingredient_name}%")).first()
                
                # Format the ingredient for display
                item_data = format_ingredient_for_display(ingredient)
                
                # Assign to correct section if mapping exists
                if ingredient_obj:
                    section_id = ingredients_to_sections.get(ingredient_obj.id)
                    if section_id and section_id in section_dict:
                        section_dict[section_id]['items'].append(item_data)
                    else:
                        # No mapping or section not found, put in uncategorized
                        section_dict['uncategorized']['items'].append(item_data)
                else:
                    # Ingredient not in database, put in uncategorized
                    section_dict['uncategorized']['items'].append(item_data)
            
            # Convert to list format for response
            result = []
            for section_id, section_data in section_dict.items():
                if section_data['items']:  # Only include non-empty sections
                    result.append({
                        'section': section_data['name'],
                        'order': section_data['order'],
                        'items': section_data['items']
                    })
            
            # Sort by section order
            result.sort(key=lambda x: x['order'])
            
            return jsonify({'grocery_list': result})
        else:
            # No store ID, just return a simple list
            return jsonify({'grocery_list': consolidated_ingredients})
            
    except Exception as e:
        logger.error(f"Error generating grocery list: {e}")
        return jsonify({"error": str(e)}), 500
    
@meal_planner_routes.route('/api/grocery_list', methods=['GET'])
def get_grocery_list_json():
    from app.routes import meal_planner_routes
    """Return the grocery list as JSON."""
    try:
        weekly_plan_id = request.args.get('weekly_plan_id')
        logger.info(f"Received request for /api/grocery_list with weekly_plan_id: {weekly_plan_id}")
        store_id = request.args.get('store_id') 
        
        # Debug: Log all ingredient-section mappings
        all_mappings = IngredientSection.query.all()
        logger.info(f"Total ingredient-section mappings in database: {len(all_mappings)}")
        for mapping in all_mappings:
            ingredient = Ingredient.query.get(mapping.ingredient_id)
            section = Section.query.get(mapping.section_id)
            if ingredient and section:
                logger.info(f"Mapping: Ingredient '{ingredient.name}' (ID: {ingredient.id}) -> Section '{section.name}' (ID: {section.id})")
        
        if not weekly_plan_id:
            return jsonify({"error": "Weekly plan ID is required"}), 400
        
        if not store_id:
            # Try to find a default store first
            default_store = Store.query.filter_by(is_default=True).first()
            if default_store:
                store_id = default_store.id
                logger.info(f"Using default store: '{default_store.name}' (ID: {store_id})")
            else:
                # Fall back to the first store
                first_store = Store.query.first()
                if first_store:
                    store_id = first_store.id
                    logger.info(f"No default store found, using first store: '{first_store.name}' (ID: {store_id})")
                else:
                    # No stores at all - return error
                    return jsonify({"error": "No stores found in database"}), 404

        weekly_plan = WeeklyPlan.query.get(weekly_plan_id)
        if not weekly_plan:
            logger.warning(f"Weekly plan not found for ID: {weekly_plan_id}")
            return jsonify({"error": "Weekly plan not found"}), 404
        
        logger.info(f"Weekly plan found: {weekly_plan.name}")

        # Gather ingredients
        all_ingredients = []
        for meal in weekly_plan.meals:
            if meal.recipe_id:
                recipe = Recipe.query.get(meal.recipe_id)
                ingredients = get_recipe_ingredients(meal.recipe_id)
                # Add recipe source info to each ingredient
                for ingredient in ingredients:
                    ingredient['recipe_id'] = meal.recipe_id
                    ingredient['from_recipe'] = recipe.name if recipe else ''
                all_ingredients.extend(ingredients)

        logger.info(f"Processing {len(all_ingredients)} ingredients for grocery list")

        # Use the new aggregation method
        aggregated_ingredients = aggregate_ingredients_with_units(all_ingredients)
        logger.info(f"Aggregated into {len(aggregated_ingredients)} unique ingredients")

        # Get all sections for this store
        sections = Section.query.filter_by(store_id=store_id).order_by(Section.order).all()
        section_dict = {section.id: {
            'name': section.name, 
            'order': section.order, 
            'sectionId': section.id,
            'items': []
        } for section in sections}

        # Add uncategorized section
        section_dict['uncategorized'] = {
            'name': 'Uncategorized', 
            'order': 999, 
            'sectionId': None,
            'items': []
        }

        # Get all ingredient-section mappings
        ingredient_mappings = IngredientSection.query.join(Section).filter(Section.store_id == store_id).all()
        ingredient_to_section_map = {mapping.ingredient_id: mapping.section_id for mapping in ingredient_mappings}

        # Map ingredients to sections
        for item in aggregated_ingredients:
            ingredient_id = item.get('id')
            ingredient_name = item.get('normalized_name', '')
            ingredient_obj = None
            
            # Find the ingredient in the database
            if ingredient_id:
                ingredient_obj = Ingredient.query.get(ingredient_id)
            
            # If no ID or not found by ID, try finding by name
            if not ingredient_obj and ingredient_name:
                ingredient_obj = Ingredient.query.filter(Ingredient.name.ilike(f"%{ingredient_name}%")).first()
            
            # Assign to correct section if mapping exists
            if ingredient_obj and ingredient_obj.id in ingredient_to_section_map:
                section_id = ingredient_to_section_map[ingredient_obj.id]
                if section_id in section_dict:
                    section_dict[section_id]['items'].append(item)
                else:
                    # No mapping or section not found, put in uncategorized
                    section_dict['uncategorized']['items'].append(item)
            else:
                # Ingredient not in database, put in uncategorized
                section_dict['uncategorized']['items'].append(item)

        # Convert to list format
        grocery_list = []
        for section_id, section_data in section_dict.items():
            if section_data['items']:  # Only include non-empty sections
                grocery_list.append({
                    'section': section_data['name'],
                    'order': section_data['order'],
                    'sectionId': section_data['sectionId'],
                    'items': section_data['items']
                })

        # Sort by section order
        grocery_list.sort(key=lambda x: x['order'])

        # Apply deduplication
        grocery_list = deduplicate_sections(grocery_list)

        # Log final structure
        logger.info("Final structure of grocery list:")
        for section in grocery_list:
            logger.info(f"Section '{section['section']}' has {len(section['items'])} items:")
            for item in section['items']:
                logger.info(f"  - {item['name']} ({item.get('id')})")

        return jsonify({"grocery_list": grocery_list})

    except Exception as e:
            logger.error(f"Error generating grocery list: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"error": "An error occurred while generating the grocery list"}), 500

@generate_grocery_bp.route('/api/generate_grocery_list', methods=['POST', 'OPTIONS'])
def generate_grocery_list():
    """
    Generate a grocery list from a list of meals without saving as a weekly plan
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        return '', 204
        
    try:
        data = request.get_json()
        meals = data.get('meals', [])
        store_id = data.get('store_id')
        
        if not meals:
            return jsonify({"error": "No meals provided"}), 400
        
        # Gather ingredients from recipes
        all_ingredients = []
        for meal in meals:
            recipe_id = meal.get('recipe_id')
            if recipe_id:
                recipe = Recipe.query.get(recipe_id)
                ingredients = get_recipe_ingredients(recipe_id)
                # Add recipe source info to each ingredient
                for ingredient in ingredients:
                    ingredient['recipe_id'] = recipe_id
                    ingredient['from_recipe'] = recipe.name if recipe else ''
                all_ingredients.extend(ingredients)
        
        logger.info(f"Retrieved {len(all_ingredients)} raw ingredients from all recipes")
        
        # Use the new aggregation method
        aggregated_ingredients = aggregate_ingredients_with_units(all_ingredients)
        logger.info(f"Aggregated into {len(aggregated_ingredients)} unique ingredients")
        
        # If store_id is provided, organize by sections
        if store_id:
            # Use a similar approach as in map_ingredients_to_sections but adapted for new format
            
            # Get all sections for this store
            sections = Section.query.filter_by(store_id=store_id).order_by(Section.order).all()
            section_dict = {section.id: {
                'name': section.name, 
                'order': section.order, 
                'sectionId': section.id,
                'items': []
            } for section in sections}
            
            # Add uncategorized section
            section_dict['uncategorized'] = {
                'name': 'Uncategorized', 
                'order': 999, 
                'sectionId': None,
                'items': []
            }
            
            # Get all ingredient-section mappings
            ingredient_mappings = IngredientSection.query.join(Section).filter(Section.store_id == store_id).all()
            ingredient_to_section_map = {mapping.ingredient_id: mapping.section_id for mapping in ingredient_mappings}
            
            # Map ingredients to sections
            for item in aggregated_ingredients:
                ingredient_id = item.get('id')
                ingredient_name = item.get('normalized_name', '')
                ingredient_obj = None
                
                # Find the ingredient in the database
                if ingredient_id:
                    ingredient_obj = Ingredient.query.get(ingredient_id)
                
                # If no ID or not found by ID, try finding by name
                if not ingredient_obj and ingredient_name:
                    ingredient_obj = Ingredient.query.filter(Ingredient.name.ilike(f"%{ingredient_name}%")).first()
                
                # Assign to correct section if mapping exists
                if ingredient_obj and ingredient_obj.id in ingredient_to_section_map:
                    section_id = ingredient_to_section_map[ingredient_obj.id]
                    if section_id in section_dict:
                        section_dict[section_id]['items'].append(item)
                    else:
                        # No mapping or section not found, put in uncategorized
                        section_dict['uncategorized']['items'].append(item)
                else:
                    # Ingredient not in database, put in uncategorized
                    section_dict['uncategorized']['items'].append(item)
            
            # Convert to list format
            grocery_list = []
            for section_id, section_data in section_dict.items():
                if section_data['items']:  # Only include non-empty sections
                    grocery_list.append({
                        'section': section_data['name'],
                        'order': section_data['order'],
                        'sectionId': section_data['sectionId'],
                        'items': section_data['items']
                    })
            
            # Sort by section order
            grocery_list.sort(key=lambda x: x['order'])
            
        else:
            # No store_id, just use a single section
            grocery_list = [{
                'section': 'All Items',
                'order': 1,
                'items': aggregated_ingredients
            }]
        
        return jsonify({"grocery_list": grocery_list})
        
    except Exception as e:
        logger.error(f"Error generating grocery list: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while generating the grocery list"}), 500
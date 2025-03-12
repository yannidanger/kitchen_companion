from flask import Blueprint, jsonify, request
from app import db
from app.models import WeeklyPlan, MealSlot, Recipe, IngredientSection, Section, Ingredient, Store
from app.utils import get_recipe_ingredients, map_ingredients_to_sections, format_ingredient_for_display
from .meal_planner import meal_planner_routes
import logging

grocery_routes = Blueprint('grocery_routes', __name__)

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
                ingredients = get_recipe_ingredients(meal.recipe_id)
                all_ingredients.extend(ingredients)
        
        # Consolidate ingredients
        ingredient_map = {}
        for ingredient in all_ingredients:
            key = (ingredient['item_name'], ingredient.get('unit', ''))
            if key not in ingredient_map:
                ingredient_map[key] = ingredient.copy()
            else:
                # Handle addition logic...
                # (Existing code here)
                pass
        
        consolidated_ingredients = list(ingredient_map.values())
        logger.debug(f"Consolidated {len(all_ingredients)} ingredients into {len(consolidated_ingredients)} unique items")
        
        # Get all section mappings
        if store_id:
            section_mappings = {}
            mappings_response = IngredientSection.query.join(Section).filter(Section.store_id == store_id).all()
            
            # Create lookup by ingredient ID
            for mapping in mappings_response:
                section_mappings[mapping.ingredient_id] = mapping.section
                
            logger.debug(f"Found {len(section_mappings)} ingredient-section mappings")
                
            # Get all sections for this store
            sections = Section.query.filter_by(store_id=store_id).order_by(Section.order).all()
            section_dict = {section.id: {'name': section.name, 'order': section.order, 'items': []} for section in sections}
            
            # Add uncategorized bucket
            section_dict['uncategorized'] = {'name': 'Uncategorized', 'order': 999, 'items': []}
            
            # Assign ingredients to sections
            for ingredient in consolidated_ingredients:
                ingredient_id = ingredient.get('id')
                ingredient_obj = None
                
                # Find the ingredient in the database if we have an ID
                if ingredient_id:
                    ingredient_obj = Ingredient.query.get(ingredient_id)
                
                # If no ID or not found by ID, try finding by name
                if not ingredient_obj and ingredient.get('item_name'):
                    ingredient_obj = Ingredient.query.filter_by(name=ingredient.get('item_name')).first()
                
                if ingredient_obj and ingredient_obj.id in section_mappings:
                    # We have a mapping for this ingredient
                    section = section_mappings[ingredient_obj.id]
                    if section.id in section_dict:
                        item_data = format_ingredient_for_display(ingredient)
                        section_dict[section.id]['items'].append(item_data)
                    else:
                        # Should not happen but fall back to uncategorized
                        item_data = format_ingredient_for_display(ingredient)
                        section_dict['uncategorized']['items'].append(item_data)
                else:
                    # No mapping found, put in uncategorized
                    item_data = format_ingredient_for_display(ingredient)
                    section_dict['uncategorized']['items'].append(item_data)
            
            # Convert to list format for response
            result = []
            for section_id, section_data in section_dict.items():
                if section_data['items']:  # Only include non-empty sections
                    result.append({
                        'section': section_data['name'],
                        'items': section_data['items']
                    })
            
            # Sort by section order
            result.sort(key=lambda x: next((s['order'] for s_id, s in section_dict.items() if s['name'] == x['section']), 999))
            
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
            default_store = Store.query.filter_by(is_default=True).first()
            if default_store:
                store_id = default_store.id
            else:
                # Or use the first store
                first_store = Store.query.first()
                if first_store:
                    store_id = first_store.id

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
        
        # Log each ingredient we're processing
        logger.info(f"Processing {len(all_ingredients)} ingredients for grocery list")
        for ing in all_ingredients:
            ing_id = ing.get('id')
            ing_name = ing.get('item_name')
            logger.info(f"Ingredient from recipe: '{ing_name}' (ID: {ing_id})")
            
            # Look up mappings for this ingredient
            if ing_id:
                mapping = IngredientSection.query.filter_by(ingredient_id=ing_id).first()
                if mapping:
                    section = Section.query.get(mapping.section_id)
                    logger.info(f"  Found mapping to section: '{section.name}' (ID: {section.id})")
                else:
                    logger.info(f"  No section mapping found for this ingredient")

        # Map ingredients to sections and format as expected by the frontend
        grocery_list = map_ingredients_to_sections(all_ingredients, store_id)
        
        # Log the final result
        logger.info(f"Final grocery list has {len(grocery_list)} sections")
        for section in grocery_list:
            logger.info(f"Section '{section['section']}': {len(section['items'])} items")
            for item in section['items']:
                logger.info(f"  - {item['name']}")
        
        # Return in the format expected by the frontend
        return jsonify({"grocery_list": grocery_list})
        
    except Exception as e:
        logger.error(f"Error generating grocery list: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": "An error occurred while generating the grocery list"}), 500

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
                ingredients = get_recipe_ingredients(meal.recipe_id)
                all_ingredients.extend(ingredients)
        
        # Consolidate ingredients
        ingredient_map = {}
        for ingredient in all_ingredients:
            key = (ingredient['item_name'], ingredient.get('unit', ''))
            if key not in ingredient_map:
                ingredient_map[key] = ingredient.copy()
            else:
                # Handle addition logic...
                # (Existing code here)
                pass
        
        consolidated_ingredients = list(ingredient_map.values())
        logger.debug(f"Consolidated {len(all_ingredients)} ingredients into {len(consolidated_ingredients)} unique items")
        
        # Get all section mappings
        if store_id:
            section_mappings = {}
            mappings_response = IngredientSection.query.join(Section).filter(Section.store_id == store_id).all()
            
            # Create lookup by ingredient ID
            for mapping in mappings_response:
                section_mappings[mapping.ingredient_id] = mapping.section
                
            logger.debug(f"Found {len(section_mappings)} ingredient-section mappings")
                
            # Get all sections for this store
            sections = Section.query.filter_by(store_id=store_id).order_by(Section.order).all()
            section_dict = {section.id: {'name': section.name, 'order': section.order, 'items': []} for section in sections}
            
            # Add uncategorized bucket
            section_dict['uncategorized'] = {'name': 'Uncategorized', 'order': 999, 'items': []}
            
            # Assign ingredients to sections
            for ingredient in consolidated_ingredients:
                ingredient_id = ingredient.get('id')
                ingredient_obj = None
                
                # Find the ingredient in the database if we have an ID
                if ingredient_id:
                    ingredient_obj = Ingredient.query.get(ingredient_id)
                
                # If no ID or not found by ID, try finding by name
                if not ingredient_obj and ingredient.get('item_name'):
                    ingredient_obj = Ingredient.query.filter_by(name=ingredient.get('item_name')).first()
                
                if ingredient_obj and ingredient_obj.id in section_mappings:
                    # We have a mapping for this ingredient
                    section = section_mappings[ingredient_obj.id]
                    if section.id in section_dict:
                        item_data = format_ingredient_for_display(ingredient)
                        section_dict[section.id]['items'].append(item_data)
                    else:
                        # Should not happen but fall back to uncategorized
                        item_data = format_ingredient_for_display(ingredient)
                        section_dict['uncategorized']['items'].append(item_data)
                else:
                    # No mapping found, put in uncategorized
                    item_data = format_ingredient_for_display(ingredient)
                    section_dict['uncategorized']['items'].append(item_data)
            
            # Convert to list format for response
            result = []
            for section_id, section_data in section_dict.items():
                if section_data['items']:  # Only include non-empty sections
                    result.append({
                        'section': section_data['name'],
                        'items': section_data['items']
                    })
            
            # Sort by section order
            result.sort(key=lambda x: next((s['order'] for s_id, s in section_dict.items() if s['name'] == x['section']), 999))
            
            return jsonify({'grocery_list': result})
        else:
            # No store ID, just return a simple list
            return jsonify({'grocery_list': consolidated_ingredients})
            
    except Exception as e:
        logger.error(f"Error generating grocery list: {e}")
        return jsonify({"error": str(e)}), 500
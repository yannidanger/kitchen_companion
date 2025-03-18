# app/routes/sub_recipes.py

from flask import Blueprint, jsonify, request
from app import db
from app.models import Recipe, RecipeComponent
import logging

sub_recipes_bp = Blueprint('sub_recipes', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@sub_recipes_bp.route('/api/sub_recipes', methods=['GET'])
@sub_recipes_bp.route('/api/sub_recipes/', methods=['GET'])
def get_available_sub_recipes():
    """
    Returns all recipes that can be used as sub-recipes
    """
    try:
        # Just return all recipes for now to get something working
        recipes = Recipe.query.all()
        result = [{'id': recipe.id, 'name': recipe.name} for recipe in recipes]
        logger.info(f"Returning {len(result)} recipes for sub-recipe dropdown")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching available sub-recipes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@sub_recipes_bp.route('/api/sub_recipes/<int:recipe_id>', methods=['GET'])
def get_sub_recipe_details(recipe_id):
    """
    Returns details for a specific sub-recipe
    """
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        return jsonify(recipe.to_dict())
    except Exception as e:
        logger.error(f"Error fetching sub-recipe details: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API endpoint to check for circular sub-recipe references
@sub_recipes_bp.route('/api/sub_recipes/check_circular', methods=['POST'])
def check_circular_reference():
    """
    Checks if adding a sub-recipe would create a circular reference
    Request body should contain: { parent_id: int, sub_recipe_id: int }
    Returns: { circular: boolean }
    """
    try:
        data = request.get_json()
        parent_id = data.get('parent_id')
        sub_recipe_id = data.get('sub_recipe_id')
        
        if not parent_id or not sub_recipe_id:
            return jsonify({'error': 'Both parent_id and sub_recipe_id are required'}), 400
            
        # Simple check: if they're the same, it's circular
        if parent_id == sub_recipe_id:
            return jsonify({'circular': True})
            
        # More complex check: recursively check if sub_recipe contains parent
        def check_recursive(current_id, target_id, checked=None):
            if checked is None:
                checked = set()
                
            # Avoid infinite loops
            if current_id in checked:
                return False
                
            checked.add(current_id)
                
            # Get all sub-recipes used in the current recipe
            components = RecipeComponent.query.filter_by(recipe_id=current_id).all()
            
            for component in components:
                # Direct circular reference
                if component.sub_recipe_id == target_id:
                    return True
                    
                # Check for indirect circular reference
                if check_recursive(component.sub_recipe_id, target_id, checked):
                    return True
                    
            return False
            
        is_circular = check_recursive(sub_recipe_id, parent_id)
        return jsonify({'circular': is_circular})
        
    except Exception as e:
        logger.error(f"Error checking circular reference: {str(e)}")
        return jsonify({'error': str(e), 'circular': True}), 500
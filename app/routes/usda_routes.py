# app/routes/usda_routes.py
from flask import Blueprint, request, jsonify
from app.models import Ingredient, db
from app.utils.usda_api import search_foods, get_food_details, simplify_food_data
from app.utils.ingredient_normalizer import normalize_ingredient_name

# Create blueprint
usda_bp = Blueprint('usda_bp', __name__)

@usda_bp.route('/api/usda/search', methods=['GET'])
def search_usda_foods():
    """Search USDA FoodData Central database"""
    query = request.args.get('query', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    page_size = int(request.args.get('pageSize', 25))
    page_number = int(request.args.get('pageNumber', 1))
    
    results = search_foods(query, page_size, page_number)
    if 'error' in results:
        return jsonify({'error': results['error']}), 400
    
    # Simplify the results for frontend use
    simplified_results = [
        simplify_food_data(food) for food in results.get('foods', [])
    ]
    
    return jsonify({
        'foods': simplified_results,
        'totalHits': results.get('totalHits', 0),
        'currentPage': results.get('currentPage', 1),
        'totalPages': results.get('totalPages', 1)
    })

@usda_bp.route('/api/usda/food/<fdc_id>', methods=['GET'])
def get_usda_food(fdc_id):
    """Get detailed information about a specific USDA food"""
    food_details = get_food_details(fdc_id)
    if 'error' in food_details:
        return jsonify({'error': food_details['error']}), 400
    
    return jsonify(simplify_food_data(food_details))

@usda_bp.route('/api/usda/save', methods=['POST'])
def save_usda_ingredient():
    """Save a USDA food as an ingredient in the database"""
    data = request.json
    if not data or 'fdc_id' not in data or 'description' not in data:
        return jsonify({'error': 'Missing required data'}), 400
    
    # Check if this USDA food is already saved
    existing = Ingredient.query.filter_by(usda_fdc_id=data['fdc_id']).first()
    if existing:
        return jsonify({'message': 'Ingredient already exists', 'ingredient': existing.to_dict()}), 200
    
    # Normalize the name for better search
    normalized_name = normalize_ingredient_name(data['description'])
    
    # Create new ingredient with USDA data
    new_ingredient = Ingredient(
        name=normalized_name,
        display_name=data['description'],
        usda_fdc_id=data['fdc_id'],
        is_custom=False,
        category=data.get('category')
    )
    
    db.session.add(new_ingredient)
    db.session.commit()
    
    return jsonify({'message': 'Ingredient saved successfully', 'ingredient': new_ingredient.to_dict()}), 201

@usda_bp.route('/api/usda/custom', methods=['POST'])
def save_custom_ingredient():
    """Save a custom ingredient not from USDA database"""
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing ingredient name'}), 400
    
    # Normalize the name
    normalized_name = normalize_ingredient_name(data['name'])
    
    # Check if a similar ingredient already exists
    existing = Ingredient.query.filter_by(name=normalized_name).first()
    if existing:
        return jsonify({'message': 'Similar ingredient already exists', 'ingredient': existing.to_dict()}), 200
    
    # Create new custom ingredient
    new_ingredient = Ingredient(
        name=normalized_name,
        display_name=data.get('display_name', data['name']),
        is_custom=True,
        category=data.get('category')
    )
    
    db.session.add(new_ingredient)
    db.session.commit()
    
    return jsonify({'message': 'Custom ingredient saved successfully', 'ingredient': new_ingredient.to_dict()}), 201
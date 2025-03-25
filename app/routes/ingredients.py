from flask import Blueprint, jsonify, request
from app import db
from app.models import Ingredient, IngredientSection, Section, RecipeIngredient
from app.utils.usda_api import search_foods, get_food_details, simplify_food_data
from app.utils.ingredient_normalizer import normalize_ingredient_name
from app.utils import logger

ingredient_routes = Blueprint('ingredient_routes', __name__)

@ingredient_routes.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    """Get all ingredients, optionally with search query, meal plan filter, and mapping status"""
    try:
        query = request.args.get('query', '').lower()
        weekly_plan_id = request.args.get('weekly_plan_id')
        store_id = request.args.get('store_id')
        unmapped_only = request.args.get('unmapped_only', 'false').lower() == 'true'
        
        # Base query
        ingredients_query = Ingredient.query
        
        # Apply weekly plan filter if provided
        if weekly_plan_id:
            from app.models import MealSlot, Recipe, RecipeIngredient
            
            # Find all recipes in the meal plan
            recipe_ids = db.session.query(MealSlot.recipe_id)\
                .filter(MealSlot.weekly_plan_id == weekly_plan_id)\
                .filter(MealSlot.recipe_id != None)\
                .distinct().all()
            
            recipe_ids = [r[0] for r in recipe_ids if r[0]]
            
            if recipe_ids:
                # Filter ingredients to only those used in the meal plan recipes
                ingredients_query = ingredients_query.join(
                    RecipeIngredient,
                    RecipeIngredient.ingredient_id == Ingredient.id
                ).filter(
                    RecipeIngredient.recipe_id.in_(recipe_ids)
                ).distinct()
            else:
                # If no recipes in meal plan, return empty list
                return jsonify([])
        
        # Apply unmapped filter if requested and store_id is provided
        if unmapped_only and store_id:
            # Get sections for this store
            sections = Section.query.filter_by(store_id=store_id).all()
            section_ids = [section.id for section in sections]
            
            # Find mapped ingredient IDs
            mapped_ingredient_ids = db.session.query(IngredientSection.ingredient_id)\
                .filter(IngredientSection.section_id.in_(section_ids))\
                .distinct().all()
            
            mapped_ingredient_ids = [i[0] for i in mapped_ingredient_ids]
            
            # Filter out mapped ingredients
            if mapped_ingredient_ids:
                ingredients_query = ingredients_query.filter(
                    ~Ingredient.id.in_(mapped_ingredient_ids)
                )
        
        # Apply search query if provided
        if query:
            ingredients_query = ingredients_query.filter(
                Ingredient.name.ilike(f"%{query}%")
            )
        
        # Order by name and execute query
        ingredients = [ing for ing in ingredients if ing.name and ing.name.strip()]
        
        return jsonify([ingredient.to_dict() for ingredient in ingredients])
    except Exception as e:
        logger.error(f"Error getting ingredients: {e}")
        return jsonify({"error": str(e)}), 500

@ingredient_routes.route('/api/ingredients/<int:ingredient_id>', methods=['GET'])
def get_ingredient(ingredient_id):
    """Get a specific ingredient by ID"""
    try:
        ingredient = Ingredient.query.get_or_404(ingredient_id)
        return jsonify(ingredient.to_dict())
    except Exception as e:
        logger.error(f"Error getting ingredient: {e}")
        return jsonify({"error": str(e)}), 500

@ingredient_routes.route('/api/ingredients/sections', methods=['GET'])
def get_ingredient_sections():
    """Get ingredient-section mappings for a store"""
    try:
        store_id = request.args.get('store_id')
        if not store_id:
            return jsonify({"error": "Store ID is required"}), 400
            
        # Get all sections for this store
        sections = Section.query.filter_by(store_id=store_id).all()
        section_ids = [section.id for section in sections]
        
        # Get all ingredient-section mappings for these sections
        mappings = IngredientSection.query.filter(
            IngredientSection.section_id.in_(section_ids)
        ).all()
        
        return jsonify([
            {
                "ingredient_id": mapping.ingredient_id,
                "section_id": mapping.section_id,
                "order": mapping.order
            }
            for mapping in mappings
        ])
    except Exception as e:
        logger.error(f"Error getting ingredient sections: {e}")
        return jsonify({"error": str(e)}), 500

@ingredient_routes.route('/api/ingredients', methods=['POST'])
def create_ingredient():
    """Create a new ingredient"""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Ingredient name is required"}), 400
            
        # Normalize the ingredient name
        normalized_name = normalize_ingredient_name(data['name'])
        
        # Check if a similar ingredient already exists
        existing = Ingredient.query.filter_by(name=normalized_name).first()
        if existing:
            return jsonify({
                "message": "Similar ingredient already exists", 
                "ingredient": existing.to_dict()
            }), 200
        
        # Create new ingredient
        new_ingredient = Ingredient(
            name=normalized_name,
            display_name=data.get('display_name', data['name']),
            is_custom=data.get('is_custom', True),
            usda_fdc_id=data.get('usda_fdc_id'),
            category=data.get('category')
        )
        
        db.session.add(new_ingredient)
        db.session.commit()
        
        return jsonify({
            "message": "Ingredient created successfully",
            "ingredient": new_ingredient.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating ingredient: {e}")
        return jsonify({"error": str(e)}), 500
    
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
    
@ingredient_routes.route('/api/ingredients/populate', methods=['GET'])
def populate_ingredients():
    """Populate some sample ingredients if the database is empty."""
    try:
        count = Ingredient.query.count()
        if count == 0:
            # Add some common ingredients
            sample_ingredients = [
                "flour", "sugar", "salt", "milk", "butter", 
                "eggs", "chicken", "beef", "pork", "apple", 
                "banana", "carrot", "onion", "garlic", "rice",
                "pasta", "cheese", "yogurt", "bread", "tomato"
            ]
            
            for name in sample_ingredients:
                ingredient = Ingredient(name=name)
                db.session.add(ingredient)
            
            db.session.commit()
            
            return jsonify({"message": f"Added {len(sample_ingredients)} sample ingredients"})
        else:
            return jsonify({"message": f"Database already has {count} ingredients"})
    except Exception as e:
        logger.error(f"Error populating ingredients: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# This updated version should replace the existing add_ingredient function in app/routes/ingredients.py

@ingredient_routes.route('/api/ingredients', methods=['POST'])
def add_ingredient():
    """Add a new ingredient."""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Ingredient name is required"}), 400
            
        from app.utils.ingredient_normalizer import normalize_ingredient_name, are_ingredients_similar
        
        # Normalize the name
        raw_name = data['name'].strip()
        normalized_name = normalize_ingredient_name(raw_name)
        
        # Check if a similar ingredient exists by checking all existing ingredients
        existing_ingredients = Ingredient.query.all()
        
        for existing in existing_ingredients:
            existing_normalized = normalize_ingredient_name(existing.name)
            if are_ingredients_similar(normalized_name, existing_normalized):
                # Return the existing ingredient
                return jsonify({
                    "message": f"Similar ingredient already exists: '{existing.name}'",
                    "ingredient": existing.to_dict(),
                    "is_existing": True
                })
        
        # Create new ingredient
        new_ingredient = Ingredient(name=raw_name)
        db.session.add(new_ingredient)
        db.session.commit()
        
        return jsonify({
            "message": "Ingredient added successfully",
            "ingredient": new_ingredient.to_dict(),
            "is_existing": False
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding ingredient: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
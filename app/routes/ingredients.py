from flask import Blueprint, jsonify, request
from app import db
from app.models import Ingredient, IngredientSection, Section, RecipeIngredient
from app.utils import logger


ingredient_routes = Blueprint('ingredient_routes', __name__)

@ingredient_routes.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    """Get all ingredients."""
    try:
        # Add a filter parameter to exclude sub-recipes
        exclude_subrec = request.args.get('exclude_subrec', 'false').lower() == 'true'
        
        ingredients = Ingredient.query.all()
        ingredients_list = []
        
        for ingredient in ingredients:
            # Skip if it's a sub-recipe
            if exclude_subrec:
                # Check if this ingredient is used as a sub-recipe in any RecipeIngredient
                is_subrecipe = db.session.query(RecipeIngredient).filter(
                    RecipeIngredient.sub_recipe_id.isnot(None),
                    RecipeIngredient.ingredient_id == ingredient.id
                ).first() is not None
                
                if is_subrecipe:
                    continue
                    
            # Skip empty names
            if not ingredient.name:
                continue
                
            ingredients_list.append(ingredient.to_dict())
        
        return jsonify(ingredients_list)
    except Exception as e:
        logger.error(f"Error getting ingredients: {e}")
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

@ingredient_routes.route('/api/ingredients', methods=['POST'])
def add_ingredient():
    """Add a new ingredient."""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Ingredient name is required"}), 400
            
        from app.utils.ingredient_normalizer import normalize_ingredient_name
        
        # Normalize the name
        raw_name = data['name'].strip()
        normalized_name = normalize_ingredient_name(raw_name)
        
        # Check if a similar ingredient exists
        existing_ingredient = Ingredient.query.filter(
            Ingredient.name.ilike(f"%{normalized_name}%")
        ).first()
        
        if existing_ingredient:
            # Return the existing ingredient
            return jsonify({
                "message": f"Similar ingredient already exists: '{existing_ingredient.name}'",
                "ingredient": existing_ingredient.to_dict(),
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
from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models import Recipe, RecipeComponent, RecipeIngredient, Ingredient
from app.utils import validate_recipe_payload, parse_fraction, logger


recipes_routes = Blueprint('recipes_routes', __name__)

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
        # Start a transaction
        db.session.begin_nested()
        
        # First, check if recipe exists
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
            
        # Find and delete related RecipeIngredient records
        RecipeIngredient.query.filter_by(recipe_id=recipe_id).delete()
        
        # Find and delete recipe components (sub-recipes) that reference this recipe
        RecipeComponent.query.filter_by(recipe_id=recipe_id).delete()
        
        # Also check for references to this recipe as a sub-recipe in other recipes
        RecipeComponent.query.filter_by(sub_recipe_id=recipe_id).delete()
        
        # Check for MealSlot references (if they exist)
        try:
            from app.models import MealSlot
            MealSlot.query.filter_by(recipe_id=recipe_id).delete()
        except (ImportError, AttributeError):
            # MealSlot might not exist or not be imported, which is fine
            logger.debug("Could not find MealSlot model, skipping meal slot cleaning")
            pass
            
        # Now we can safely delete the recipe
        db.session.delete(recipe)
        
        # Commit the transaction
        db.session.commit()
        
        logger.info(f"Recipe with ID {recipe_id} successfully deleted")
        return jsonify({'message': 'Recipe deleted successfully'}), 200
    except Exception as e:
        # Roll back in case of an error
        db.session.rollback()
        
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
        logger.error(error_details)
        
        return jsonify({'error': str(e)}), 500

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
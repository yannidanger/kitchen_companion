# app/utils/ingredient_normalizer.py
import re
import logging

logger = logging.getLogger(__name__)

def normalize_ingredient_name(name):
    """
    Normalize ingredient names for consistent storage and comparison.
    - Convert to lowercase
    - Remove extra whitespace
    - Remove common prefixes like "fresh", "frozen", etc. when appropriate
    - Handle plurals to a degree
    """
    if not name:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common descriptive prefixes
    prefixes_to_remove = [
        r'^fresh ', r'^dried ', r'^frozen ', r'^canned ', 
        r'^whole ', r'^chopped ', r'^diced ', r'^sliced '
    ]
    
    for prefix in prefixes_to_remove:
        normalized = re.sub(prefix, '', normalized)
    
    # Basic plural handling (not comprehensive but handles common cases)
    plurals = {
        'tomatoes': 'tomato',
        'potatoes': 'potato',
        'carrots': 'carrot',
        'onions': 'onion',
        'apples': 'apple',
        'bananas': 'banana',
        'eggs': 'egg',
        'lemons': 'lemon',
        'oranges': 'orange',
    }
    
    # Check if the normalized name is in our plurals dictionary
    if normalized in plurals:
        normalized = plurals[normalized]
    # Or handle simple plural forms (ending with 's')
    elif normalized.endswith('s') and not normalized.endswith('ss'):
        singular = normalized[:-1]
        # Only convert to singular if it makes sense
        # (avoid changing things like "rice" to "ric")
        if len(singular) > 2:
            normalized = singular
    
    logger.debug(f"Normalized '{name}' to '{normalized}'")
    return normalized

def find_matching_ingredient(name, ingredients_list):
    """
    Find a matching ingredient in the database based on normalized name.
    Returns ingredient_id if found, None otherwise.
    """
    from app.models import Ingredient
    
    normalized = normalize_ingredient_name(name)
    
    # First try exact match on normalized name
    for ingredient in ingredients_list:
        if normalize_ingredient_name(ingredient.name) == normalized:
            return ingredient.id
    
    # Try database lookup with case-insensitive search
    ingredient = Ingredient.query.filter(Ingredient.name.ilike(f"%{normalized}%")).first()
    if ingredient:
        return ingredient.id
    
    return None

def get_canonical_name(name, ingredient_id=None):
    """
    Get the canonical (database) name for an ingredient if it exists,
    otherwise return the normalized version of the provided name.
    """
    from app.models import Ingredient
    
    if ingredient_id:
        ingredient = Ingredient.query.get(ingredient_id)
        if ingredient:
            return ingredient.name
    
    # Try to find by name
    normalized = normalize_ingredient_name(name)
    ingredient = Ingredient.query.filter(Ingredient.name.ilike(f"%{normalized}%")).first()
    
    if ingredient:
        return ingredient.name
    
    # If we can't find a canonical name, at least normalize it
    return normalized

def are_ingredients_similar(name1, name2):
    """
    Determine if two ingredient names likely refer to the same ingredient.
    """
    normalized1 = normalize_ingredient_name(name1)
    normalized2 = normalize_ingredient_name(name2)
    
    # Direct match after normalization
    if normalized1 == normalized2:
        return True
    
    # Check if one is contained within the other
    if normalized1 in normalized2 or normalized2 in normalized1:
        return True
    
    # Add more similarity checks as needed
    
    return False
# app/utils/ingredient_normalizer.py
import re
import logging
import unicodedata
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Dictionary of common ingredient spelling variations and corrections
INGREDIENT_SPELLING_VARIATIONS = {
    # Accented characters and diacritical marks
    'jalapeno': 'jalapeño',
    'jalapenos': 'jalapeño',
    'habanero': 'habanero',
    'acai': 'açaí',
    'acaiberry': 'açaí berry',
    'pina': 'piña',
    'pina colada': 'piña colada',
    'creme fraiche': 'crème fraîche',
    'creme fraiche': 'crème fraîche',
    
    # Common misspellings
    'tumeric': 'turmeric',
    'cinamon': 'cinnamon',
    'cinammon': 'cinnamon',
    'corriander': 'coriander',
    'cumin seed': 'cumin',
    'cummin': 'cumin',
    'chili': 'chile',
    'chilli': 'chile',
    'chilies': 'chiles',
    'chillis': 'chiles',
    'chillies': 'chiles',
    'scallion': 'green onion',
    'spring onion': 'green onion',
    
    # Branded/generic equivalents
    'kleenex': 'tissue',
    'qtip': 'cotton swab',
    'ziploc': 'resealable bag',
    'saran wrap': 'plastic wrap',
    
    # Same ingredients with different names
    'bell pepper': 'pepper',
    'capsicum': 'pepper',
    'rock sugar': 'sugar',
    'granulated sugar': 'sugar',
    'muscovado': 'brown sugar',
    'demerara': 'brown sugar',
    'confectioners sugar': 'powdered sugar',
    'icing sugar': 'powdered sugar',
}

# Common names to normalize when they appear at the beginning of an ingredient
PREFIX_VARIATIONS = {
    'minced': '',
    'diced': '',
    'chopped': '',
    'sliced': '',
    'grated': '',
    'shredded': '',
    'julienned': '',
    'crushed': '',
    'ground': '',
    'mashed': '',
    'puréed': '',
    'pureed': '',
    'freshly': '',
    'fresh': '',
    'frozen': '',
    'canned': '',
    'dried': '',
    'powdered': '',
    'raw': '',
    'cooked': '',
    'boiled': '',
    'steamed': '',
    'roasted': '',
    'grilled': '',
    'baked': '',
    'fried': '',
    'whole': '',
    'peeled': '',
    'skinless': '',
    'boneless': '',
}

# Comprehensive plurals dictionary
PLURALS = {
    'tomatoes': 'tomato',
    'potatoes': 'potato',
    'carrots': 'carrot',
    'onions': 'onion',
    'apples': 'apple',
    'bananas': 'banana',
    'eggs': 'egg',
    'lemons': 'lemon',
    'oranges': 'orange',
    'peppers': 'pepper',
    'beans': 'bean',
    'peas': 'pea',
    'olives': 'olive',
    'mushrooms': 'mushroom',
    'strawberries': 'strawberry',
    'raspberries': 'raspberry',
    'blueberries': 'blueberry',
    'blackberries': 'blackberry',
    'cherries': 'cherry',
    'grapes': 'grape',
    'avocados': 'avocado',
    'cucumbers': 'cucumber',
    'zucchinis': 'zucchini',
    'eggplants': 'eggplant',
    'aubergines': 'aubergine',
    'herbs': 'herb',
    'spices': 'spice',
    'cloves': 'clove',
    'garlic cloves': 'garlic clove',
    'jalapeños': 'jalapeño',
    'jalapenos': 'jalapeño',
    'chiles': 'chile',
    'chilies': 'chile',
    'chilis': 'chile',
    'chillies': 'chile',
    'chillis': 'chile',
    'scallions': 'scallion',
    'green onions': 'green onion',
    'spring onions': 'spring onion',
    'shallots': 'shallot',
    'noodles': 'noodle',
}

def normalize_string(text):
    """Basic string normalization: lowercase, strip, and remove accents"""
    if not text:
        return ""
    
    # Convert to lowercase and strip whitespace
    text = text.lower().strip()
    
    # Remove extra whitespace within the string
    text = re.sub(r'\s+', ' ', text)
    
    return text

def remove_accents(text):
    """Remove accents from text, but maintain the base character"""
    if not text:
        return ""
    
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                  if not unicodedata.combining(c))

def remove_prefixes(text, prefixes=None):
    """Remove common descriptive prefixes"""
    if not text:
        return text
        
    if prefixes is None:
        prefixes = PREFIX_VARIATIONS
    
    words = text.split()
    if not words:
        return text
        
    # Check if the first word is a prefix to remove
    if words[0] in prefixes:
        return ' '.join(words[1:])
    
    return text

def handle_plurals(text, plurals=None):
    """Convert plural forms to singular"""
    if not text:
        return text
        
    if plurals is None:
        plurals = PLURALS
    
    # Check direct match in plurals dictionary
    if text in plurals:
        return plurals[text]
    
    # Handle general English plurals ending with 's'
    if text.endswith('s') and not text.endswith('ss'):
        # Don't apply to very short words or words ending in 'ss'
        singular = text[:-1]
        if len(singular) > 2:
            # Don't singularize words like "rice" to "ric"
            return singular
    
    return text

def correct_spelling(text, variations=None):
    """Correct common spelling variations and ingredient name differences"""
    if not text:
        return text
        
    if variations is None:
        variations = INGREDIENT_SPELLING_VARIATIONS
    
    # Check for exact match in variations dictionary
    if text in variations:
        return variations[text]
    
    # Look for partial matches in multi-word ingredients
    for variation, correction in variations.items():
        if variation in text:
            # Replace the variation with the correction
            text = text.replace(variation, correction)
            
    return text

def similarity_ratio(a, b):
    """Calculate string similarity ratio between 0 and 1"""
    return SequenceMatcher(None, a, b).ratio()

def normalize_ingredient_name(name):
    """
    Enhanced normalization for ingredient names:
    - Convert to lowercase
    - Remove extra whitespace
    - Correct common spelling variations
    - Remove common prefixes
    - Handle plurals
    """
    if not name:
        return ""
    
    # Basic normalization
    normalized = normalize_string(name)
    
    # Correct common spelling variations and regional names
    normalized = correct_spelling(normalized)
    
    # Remove common descriptive prefixes
    normalized = remove_prefixes(normalized)
    
    # Handle plurals
    normalized = handle_plurals(normalized)
    
    logger.debug(f"Normalized '{name}' to '{normalized}'")
    return normalized

def find_matching_ingredient(name, ingredients_list):
    """
    Find a matching ingredient in the database based on normalized name.
    Returns ingredient_id if found, None otherwise.
    Uses more sophisticated matching to handle variations.
    """
    from app.models import Ingredient
    
    normalized = normalize_ingredient_name(name)
    normalized_no_accents = remove_accents(normalized)
    
    # First try exact match on normalized name
    for ingredient in ingredients_list:
        ingredient_normalized = normalize_ingredient_name(ingredient.name)
        if ingredient_normalized == normalized:
            return ingredient.id
    
    # Try case-insensitive partial matching
    for ingredient in ingredients_list:
        ingredient_normalized = normalize_ingredient_name(ingredient.name)
        # Check if normalized names are similar enough (partial match)
        if (normalized in ingredient_normalized or 
            ingredient_normalized in normalized or
            similarity_ratio(normalized, ingredient_normalized) > 0.8):
            return ingredient.id
    
    # Try without accents (for characters like ñ)
    for ingredient in ingredients_list:
        ingredient_normalized = normalize_ingredient_name(ingredient.name)
        ingredient_no_accents = remove_accents(ingredient_normalized)
        if normalized_no_accents == ingredient_no_accents:
            return ingredient.id
    
    # Fallback to database lookup with case-insensitive search
    ingredient = Ingredient.query.filter(Ingredient.name.ilike(f"%{normalized}%")).first()
    if ingredient:
        return ingredient.id
    
    # Try database lookup without accents as a last resort
    normalized_pattern = remove_accents(normalized).replace('%', '\%').replace('_', '\_')
    ingredient = Ingredient.query.filter(
        remove_accents(Ingredient.name.lower()).ilike(f"%{normalized_pattern}%")
    ).first()
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
    
    # Try to find by name with enhanced matching
    normalized = normalize_ingredient_name(name)
    
    # Try exact match first
    ingredient = Ingredient.query.filter(normalize_ingredient_name(Ingredient.name) == normalized).first()
    if not ingredient:
        # Then try partial match
        ingredient = Ingredient.query.filter(Ingredient.name.ilike(f"%{normalized}%")).first()
    
    if ingredient:
        return ingredient.name
    
    # If we can't find a canonical name, return the original name
    # This preserves user input when we don't have a match
    return name

def are_ingredients_similar(name1, name2):
    """
    Determine if two ingredient names likely refer to the same ingredient.
    Uses multiple similarity measures for better matching.
    """
    normalized1 = normalize_ingredient_name(name1)
    normalized2 = normalize_ingredient_name(name2)
    
    # Direct match after normalization
    if normalized1 == normalized2:
        return True
    
    # Check if one is contained within the other
    if normalized1 in normalized2 or normalized2 in normalized1:
        return True
    
    # Try without accents
    if remove_accents(normalized1) == remove_accents(normalized2):
        return True
    
    # Use similarity ratio for fuzzy matching
    # (threshold of 0.8 means 80% similar)
    if similarity_ratio(normalized1, normalized2) > 0.8:
        return True
    
    return False

    # app/utils/ingredient_normalizer.py (add to existing file)

def normalize_with_usda(name, usda_fdc_id=None):
    """
    Enhanced normalization that considers USDA data when available
    
    Args:
        name (str): Ingredient name
        usda_fdc_id (str): USDA FDC ID if available
        
    Returns:
        str: Normalized ingredient name
    """
    from app.models import Ingredient
    
    # If we have a USDA ID, use that as the primary identifier
    if usda_fdc_id:
        # Check if this USDA food is already in our database
        existing = Ingredient.query.filter_by(usda_fdc_id=usda_fdc_id).first()
        if existing:
            return existing.name
        
        # If not in database but we have USDA ID, use the name as-is
        # but still normalize it for consistency
        return normalize_ingredient_name(name)
    
    # No USDA ID, use standard normalization
    return normalize_ingredient_name(name)

def find_matching_ingredient_enhanced(name, usda_fdc_id=None):
    """
    Find a matching ingredient with enhanced USDA support
    
    Args:
        name (str): Ingredient name
        usda_fdc_id (str): USDA FDC ID if available
        
    Returns:
        Ingredient object or None
    """
    from app.models import Ingredient
    
    # If we have a USDA ID, that's the primary match criteria
    if usda_fdc_id:
        ingredient = Ingredient.query.filter_by(usda_fdc_id=usda_fdc_id).first()
        if ingredient:
            return ingredient
    
    # Fallback to name-based matching
    normalized = normalize_ingredient_name(name)
    
    # Try exact match on normalized name
    ingredient = Ingredient.query.filter(
        Ingredient.name == normalized
    ).first()
    if ingredient:
        return ingredient
    
    # Try partial match
    ingredient = Ingredient.query.filter(
        Ingredient.name.ilike(f"%{normalized}%")
    ).first()
    if ingredient:
        return ingredient
    
    return None
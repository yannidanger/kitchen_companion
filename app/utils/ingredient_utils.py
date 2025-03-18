# app/utils/ingredient_utils.py

def sanitize_ingredient_name(name):
    """
    Sanitize ingredient names for consistency:
    - Convert to lowercase
    - Trim whitespace
    - Remove common prefixes like "fresh", "dried", etc. for matching
    
    Returns:
        tuple: (display_name, normalized_name)
            display_name: Preserved capitalization for display
            normalized_name: Lowercase, trimmed version for matching
    """
    if not name:
        return ("", "")
    
    # Preserve original with proper capitalization for display
    display_name = name.strip()
    
    # Create normalized version for matching and storage
    normalized_name = name.lower().strip()
    
    # Remove common qualifiers for matching purposes
    matching_name = normalized_name
    prefixes_to_remove = ["fresh ", "dried ", "frozen ", "canned ", "whole "]
    for prefix in prefixes_to_remove:
        if matching_name.startswith(prefix):
            matching_name = matching_name[len(prefix):]
    
    return (display_name, normalized_name, matching_name)


def sanitize_unit(unit):
    """
    Standardize unit names (e.g., "tbsp" and "tablespoon" should match)
    """
    if not unit:
        return ""
    
    unit = unit.lower().strip()
    
    # Map common unit variations to standard forms
    unit_mapping = {
        # Volume
        "tablespoon": "tbsp",
        "tablespoons": "tbsp",
        "tbsps": "tbsp", 
        "tbs": "tbsp",
        "teaspoon": "tsp",
        "teaspoons": "tsp",
        "tsps": "tsp",
        "cup": "cup",
        "cups": "cup",
        "fluid ounce": "fl oz",
        "fluid ounces": "fl oz",
        "fl. oz.": "fl oz",
        "pint": "pt",
        "pints": "pt",
        "quart": "qt",
        "quarts": "qt",
        "gallon": "gal",
        "gallons": "gal",
        "milliliter": "ml",
        "milliliters": "ml",
        "liter": "l",
        "liters": "l",
        # Weight
        "ounce": "oz",
        "ounces": "oz",
        "pound": "lb",
        "pounds": "lb",
        "lbs": "lb",
        "gram": "g",
        "grams": "g",
        "kilogram": "kg",
        "kilograms": "kg",
        # Count
        "each": "",
        "unit": "",
        "units": "",
        "whole": "",
        "package": "pkg",
        "packages": "pkg",
        "bunch": "bunch",
        "bunches": "bunch",
        "sprig": "sprig",
        "sprigs": "sprig",
        "clove": "clove",
        "cloves": "clove",
        "head": "head",
        "heads": "head",
        "bulb": "bulb",
        "bulbs": "bulb",
    }
    
    # Return the standardized unit or the original if not found
    return unit_mapping.get(unit, unit)
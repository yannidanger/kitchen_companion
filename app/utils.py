from fractions import Fraction
import logging
import re
from app.models import Recipe, Store, Section, IngredientSection, Ingredient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Function to validate recipe payload
def validate_recipe_payload(data):
    required_fields = ['name', 'ingredients']
    for field in required_fields:
        if field not in data or not data[field]:
            return f"Missing or empty required field: {field}"
    return None

# Function to parse a fraction string
def parse_fraction(fraction_str):
    """Parse a fraction string into numerator and denominator."""
    if not fraction_str or fraction_str.strip() == '':
        return None, None, None, False

    fraction_str = str(fraction_str).strip()

    try:
        return float(fraction_str), None, None, False
    except ValueError:
        pass

    try:
        mixed_match = re.match(r'(\d+)\s+(\d+)/(\d+)', fraction_str)
        if mixed_match:
            whole = int(mixed_match.group(1))
            numerator = int(mixed_match.group(2))
            denominator = int(mixed_match.group(3))
            numerator = whole * denominator + numerator
            return float(numerator) / float(denominator), numerator, denominator, True

        fraction_match = re.match(r'(\d+)/(\d+)', fraction_str)
        if fraction_match:
            numerator = int(fraction_match.group(1))
            denominator = int(fraction_match.group(2))
            return float(numerator) / float(denominator), numerator, denominator, True

        frac = Fraction(fraction_str)
        return float(frac), frac.numerator, frac.denominator, True
    except (ValueError, ZeroDivisionError):
        return None, None, None, False

# Existing utility functions in your utils.py

def parse_ingredients(raw_data):
    """Parse raw ingredient data into a standardized format."""
    def parse_quantity(quantity_str):
        """Convert a quantity string to a float, supporting fractions."""
        if not quantity_str.strip():  # Handle empty quantities
            return None, ""
        try:
            return float(Fraction(quantity_str)), quantity_str
        except ValueError:
            raise ValueError(f"Invalid quantity format: {quantity_str}")

    ingredients = []
    for ingredient in raw_data:
        quantity_float, original_quantity = parse_quantity(ingredient.get('quantity', '').strip())
        ingredients.append({
            'food_name': ingredient['item_name'].strip(),
            'quantity': quantity_float,  # Decimal value for storage
            'original_quantity': original_quantity,  # Original value for display
            'unit': ingredient.get('unit', '').strip(),
            'size': ingredient.get('size', '').strip(),
            'descriptor': ingredient.get('descriptor', '').strip(),
            'additional_descriptor': ingredient.get('additional_descriptor', '').strip(),
        })
    return ingredients

def convert_to_base_unit(quantity, unit):
    """Convert the given quantity and unit to a base unit."""
    unit_conversions = {
        # Volume
        "Tablespoon (tbsp)": ("ml", 14.7868),
        "Teaspoon (tsp)": ("ml", 4.92892),
        "Cup": ("ml", 240),
        "Liter (l)": ("ml", 1000),
        "Milliliter (ml)": ("ml", 1),

        # Weight/Mass
        "Ounce (oz)": ("grams", 28.3495),
        "Pound (lb)": ("grams", 453.592),
        "Gram (g)": ("grams", 1),
        "Kilogram (kg)": ("grams", 1000),
        "Milligram (mg)": ("grams", 0.001),

        # Count/Units
        "unitless": ("unitless", 1),
        "Piece": ("piece", 1),
        "Dozen": ("piece", 12),

        # Miscellaneous/Traditional
        "Sprig": ("Sprig", 1),
        "Block": ("Block", 1),
        "Dash": ("Dash", 1),
        "Pinch": ("Pinch", 1),
        "Drop": ("Drop", 1),
        "Smidgen": ("Smidgen", 1),
        "Juice of": ("Juice of", 1),
        "Zest of": ("Zest of", 1),

        # Specialty Units
        "Stick": ("Stick", 1),
        "Can": ("Can", 1),
        "Packet": ("Packet", 1),
    }

    if unit not in unit_conversions:
        raise ValueError(f"Unknown unit: {unit}")

    base_unit, conversion_factor = unit_conversions[unit]
    base_quantity = quantity * conversion_factor
    return base_quantity, base_unit

def aggregate_ingredients(ingredients):
    """Aggregate ingredients by converting quantities to base units and summing them."""
    aggregated = {}
    for ingredient in ingredients:
        try:
            food_name = ingredient.get('food_name')
            quantity = ingredient.get('quantity')
            unit = ingredient.get('unit')

            if not food_name or quantity is None or not unit:
                logging.warning(f"Skipping invalid ingredient: {ingredient}")
                continue

            try:
                base_quantity, base_unit = convert_to_base_unit(quantity, unit)
            except ValueError as e:
                logging.error(f"Error converting unit '{unit}' for '{food_name}': {e}")
                continue

            key = (food_name, base_unit)
            aggregated[key] = aggregated.get(key, 0) + base_quantity

        except Exception as e:
            logging.error(f"Unexpected error processing ingredient {ingredient}: {e}")
            continue

    return aggregated

def render_grocery_list(aggregated_ingredients):
    """Render the grocery list in a human-readable format."""
    def format_quantity(quantity):
        if isinstance(quantity, float):
            return f"{quantity:.2f}" if quantity % 1 else f"{int(quantity)}"
        return str(quantity)

    rendered_list = []
    for ingredient in aggregated_ingredients:
        item_name = ingredient["item_name"]
        quantity = ingredient["quantity"]
        unit = ingredient["unit"]
        formatted_quantity = format_quantity(quantity)
        rendered_list.append(f"{formatted_quantity} {unit} of {item_name}")

    return "\n".join(rendered_list)

def get_recipe_ingredients(recipe_id, quantity_multiplier=1.0, visited=None):
    """Recursively get all ingredients for a recipe, including from sub-recipes."""
    if visited is None:
        visited = set()
    
    # Prevent circular references
    if recipe_id in visited:
        return []
    
    visited.add(recipe_id)
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return []
    
    result = []
    
    # Add direct ingredients
    for ingredient in recipe.ingredients:
        if ingredient.ingredient:  # Regular ingredient
            quantity_info = {
                'quantity': (ingredient.quantity or 0) * quantity_multiplier,
                'is_fraction': ingredient.is_fraction
            }
            
            # Handle fractions
            if ingredient.is_fraction and ingredient.quantity_numerator is not None and ingredient.quantity_denominator is not None:
                # Scale the fraction by the multiplier
                numerator = int(ingredient.quantity_numerator * quantity_multiplier)
                denominator = ingredient.quantity_denominator
                quantity_info['quantity_numerator'] = numerator
                quantity_info['quantity_denominator'] = denominator
                
                # Generate a display string for the fraction
                if numerator >= denominator:
                    whole_part = numerator // denominator
                    remainder = numerator % denominator
                    if remainder == 0:
                        fraction_display = str(whole_part)
                    else:
                        fraction_display = f"{whole_part} {remainder}/{denominator}"
                else:
                    fraction_display = f"{numerator}/{denominator}"
                    
                precision_text = f"({fraction_display} {ingredient.unit or ''})"
            else:
                # Handle regular decimal quantities
                precision_text = f"({(ingredient.quantity or 0) * quantity_multiplier} {ingredient.unit or ''})"
                
            result.append({
                "id": ingredient.ingredient.id,
                "item_name": ingredient.ingredient.name,
                "quantity": (ingredient.quantity or 0) * quantity_multiplier,
                "unit": ingredient.unit or "",
                "main_text": ingredient.ingredient.name,
                "precision_text": precision_text,
                "is_fraction": ingredient.is_fraction,
                "quantity_numerator": ingredient.quantity_numerator,
                "quantity_denominator": ingredient.quantity_denominator
            })
    
    # Add ingredients from sub-recipes
    for component in recipe.components:
        if component.sub_recipe_id:
            sub_quantity = component.quantity or 1.0
            sub_ingredients = get_recipe_ingredients(
                component.sub_recipe_id, 
                quantity_multiplier * sub_quantity,
                visited.copy()
            )
            result.extend(sub_ingredients)
    
    return result

def map_ingredients_to_sections(ingredients):
    """Maps ingredients to store sections with proper ordering."""
    logger.debug(f"Mapping {len(ingredients)} ingredients to sections")
    # Get default store ID (for simplicity)
    default_store = Store.query.filter_by(is_default=True).first()
    store_id = default_store.id if default_store else None
    
    if not store_id:
        # Fallback to first store
        first_store = Store.query.first()
        store_id = first_store.id if first_store else None
    
    # Get section mappings for ingredients
    ingredient_section_map = {}
    if store_id:
        # Get sections from this store
        sections = Section.query.filter_by(store_id=store_id).all()
        section_dict = {section.id: {
            'name': section.name, 
            'order': section.order,
            'items': []
        } for section in sections}
        
        # Get all ingredient-section mappings
        all_mappings = IngredientSection.query.all()
        
        # Create lookup by ingredient ID
        for mapping in all_mappings:
            ingredient_section_map[mapping.ingredient_id] = mapping.section_id
    else:
        # No store available, create empty section dict
        sections = Section.query.all()
    section_dict = {section.id: {
        'name': section.name, 
        'order': section.order,
        'items': []
    } for section in sections}
    logger.debug(f"Found {len(sections)} sections")
    
    # Add uncategorized container
    uncategorized_items = []
    
    # Process each ingredient
    for ingredient in ingredients:
        ingredient_id = ingredient.get("id")
        ingredient_name = ingredient.get("item_name", "")
        logger.debug(f"Processing ingredient: {ingredient_name} (ID: {ingredient_id})")

        ingredient_section = None
        if ingredient_id:
            ingredient_section = IngredientSection.query.filter_by(ingredient_id=ingredient_id).first()
        
        if ingredient_section and ingredient_section.section_id in section_dict:
            section_name = section_dict[ingredient_section.section_id]['name']
            logger.debug(f"  Assigning to section: {section_name} (ID: {ingredient_section.section_id})")
            # Add to the appropriate section
            section_dict[ingredient_section.section_id]['items'].append({
                "name": ingredient.get("main_text", ingredient.get("item_name", "")),
                "quantity": ingredient.get("quantity", 0),
                "unit": ingredient.get("unit", ""),
                "fraction_str": ingredient.get("fraction_str"),
                "precision_text": ingredient.get("precision_text")
            })
        else:
            logger.debug(f"  Adding to uncategorized (no mapping found)")
            # Add to uncategorized
            uncategorized_items.append({
                "name": ingredient.get("main_text", ingredient.get("item_name", "")),
                "quantity": ingredient.get("quantity", 0),
                "unit": ingredient.get("unit", ""),
                "fraction_str": ingredient.get("fraction_str"),
                "precision_text": ingredient.get("precision_text")
            })
        
        # Find the ingredient in the database (might need to look up by name)
        db_ingredient = None
        if ingredient_id:
            db_ingredient = Ingredient.query.get(ingredient_id)
        
        if not db_ingredient and ingredient.get('item_name'):
            db_ingredient = Ingredient.query.filter_by(name=ingredient.get('item_name')).first()
        
        display_item = {
            "name": ingredient.get("main_text", ingredient.get("item_name", "")),
            "quantity": ingredient.get("quantity", 0),
            "unit": ingredient.get("unit", ""),
            "fraction_str": ingredient.get("fraction_str", ""),
            "precision_text": ingredient.get("precision_text", "")
        }
        
        if db_ingredient and db_ingredient.id in ingredient_section_map:
            # We have a mapping for this ingredient
            section_id = ingredient_section_map[db_ingredient.id]
            if section_id in section_dict:
                section_dict[section_id]['items'].append(display_item)
            else:
                # Section doesn't exist anymore, put in uncategorized
                uncategorized_items.append(display_item)
        else:
            # No mapping found
            uncategorized_items.append(display_item)
    
    # Convert to list format expected by frontend
    result = []
    
    # Add sections with items
    for section_id, section_data in section_dict.items():
        if section_data['items']:
            result.append({
                "section": section_data['name'],
                "order": section_data['order'],
                "items": section_data['items']
            })
    
    # Add uncategorized section if it has items
    if uncategorized_items:
        result.append({
            "section": "Uncategorized",
            "order": 999,
            "items": uncategorized_items
        })
    
    # Sort sections by order
    result.sort(key=lambda x: x.get('order', 999))
    
    return result

def format_ingredient_for_display(ingredient):
    """Format an ingredient dictionary for display in the grocery list."""
    display_item = {
        'id': ingredient.get('id'),
        'name': ingredient.get('item_name'),
        'quantity': ingredient.get('quantity'),
        'unit': ingredient.get('unit', ''),
        'is_fraction': ingredient.get('is_fraction', False)
    }
    
    # Add fraction string if available
    if ingredient.get('is_fraction') and ingredient.get('quantity_numerator') and ingredient.get('quantity_denominator'):
        numerator = ingredient['quantity_numerator']
        denominator = ingredient['quantity_denominator']
        
        if numerator >= denominator:
            whole_part = numerator // denominator
            remainder = numerator % denominator
            if remainder == 0:
                display_item['fraction_str'] = str(whole_part)
            else:
                display_item['fraction_str'] = f"{whole_part} {remainder}/{denominator}"
        else:
            display_item['fraction_str'] = f"{numerator}/{denominator}"
    
    return display_item
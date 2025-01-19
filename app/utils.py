from fractions import Fraction
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Adjust log level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def parse_ingredients(raw_data):
    """
    Parse raw ingredient data into a standardized format.

    Args:
        raw_data (list[dict]): List of ingredient dictionaries.

    Returns:
        list[dict]: Parsed list of ingredients in dictionary format.
    """
    from fractions import Fraction

    def parse_quantity(quantity_str):
        """Convert a quantity string to a float, supporting fractions."""
        if not quantity_str.strip():  # Handle empty quantities
            return None, ""
        try:
            # Return both the float value and the original string
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
        "Dozen": ("piece", 12),  # Dozen converted to pieces

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
    """
    Aggregate ingredients by converting quantities to base units and summing them.

    Args:
        ingredients (list[dict]): List of ingredient dictionaries with 'food_name', 'quantity', and 'unit'.

    Returns:
        dict: Aggregated ingredients with quantities in base units.
    """
    aggregated = {}
    for ingredient in ingredients:
        try:
            # Extract ingredient details
            food_name = ingredient.get('food_name')
            quantity = ingredient.get('quantity')
            unit = ingredient.get('unit')

            if not food_name or quantity is None or not unit:
                logging.warning(f"Skipping invalid ingredient: {ingredient}")
                continue  # Skip invalid ingredients

            # Convert to base unit
            try:
                base_quantity, base_unit = convert_to_base_unit(quantity, unit)
            except ValueError as e:
                logging.error(f"Error converting unit '{unit}' for '{food_name}': {e}")
                continue  # Skip ingredients with unrecognized units

            # Aggregate quantities
            key = (food_name, base_unit)
            aggregated[key] = aggregated.get(key, 0) + base_quantity

        except Exception as e:
            logging.error(f"Unexpected error processing ingredient {ingredient}: {e}")
            continue  # Skip on unexpected errors

    return aggregated

def render_grocery_list(aggregated_ingredients):
    """
    Render the grocery list in a human-readable format.

    Args:
        aggregated_ingredients (list[dict]): List of aggregated ingredients with 'item_name', 'unit', and 'quantity'.

    Returns:
        str: Formatted grocery list as a string.
    """
    def format_quantity(quantity):
        # Round quantities for display
        if isinstance(quantity, float):
            return f"{quantity:.2f}" if quantity % 1 else f"{int(quantity)}"
        return str(quantity)

    # Format each ingredient
    rendered_list = []
    for ingredient in aggregated_ingredients:
        item_name = ingredient["item_name"]
        quantity = ingredient["quantity"]
        unit = ingredient["unit"]
        formatted_quantity = format_quantity(quantity)
        rendered_list.append(f"{formatted_quantity} {unit} of {item_name}")
    
    return "\n".join(rendered_list)



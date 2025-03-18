# app/utils/grocery_list_aggregation.py

from .ingredient_utils import sanitize_ingredient_name, sanitize_unit
from .unit_conversion import can_convert, convert_units, convert_ingredient_specific
from .fraction_utils import decimal_to_fraction_parts

def aggregate_grocery_list(ingredient_list):
    """
    Aggregate similar ingredients in a grocery list
    
    Args:
        ingredient_list: List of dictionaries containing ingredient data
            Each dict should have: name, quantity, unit, etc.
    
    Returns:
        List of aggregated ingredients with original measurements
    """
    normalized_ingredients = {}  # Map of normalized name to ingredient data
    
    for item in ingredient_list:
        # Get required fields
        name = item.get('name', '')
        quantity = item.get('quantity', 0)
        unit = sanitize_unit(item.get('unit', ''))
        
        # Skip items without a name or quantity
        if not name or not quantity:
            continue
            
        # Normalize the ingredient name for matching
        display_name, normalized_name, matching_name = sanitize_ingredient_name(name)
        
        # Create key for aggregation - for now, just use the matching name
        ingredient_key = matching_name
        
        # If this ingredient hasn't been seen before, add it
        if ingredient_key not in normalized_ingredients:
            normalized_ingredients[ingredient_key] = {
                'display_name': display_name,
                'normalized_name': normalized_name,
                'matching_name': matching_name,
                'total_quantity': 0,
                'base_unit': None,
                'measurements': [],
                'original_items': []
            }
        
        # Try to convert the quantity to the base unit if already established
        ingredient_data = normalized_ingredients[ingredient_key]
        
        # Add the original item for reference
        ingredient_data['original_items'].append(item)
        
        # Store the original measurement
        original_measurement = {
            'quantity': quantity,
            'unit': unit,
            'recipe_id': item.get('recipe_id'),
            'recipe_name': item.get('recipe_name', '')
        }
        ingredient_data['measurements'].append(original_measurement)
        
        # Try to aggregate quantities 
        if not ingredient_data['base_unit']:
            # First item: establish the base unit
            ingredient_data['base_unit'] = unit
            ingredient_data['total_quantity'] = quantity
        elif unit == ingredient_data['base_unit']:
            # Same unit: simply add the quantities
            ingredient_data['total_quantity'] += quantity
        elif can_convert(unit, ingredient_data['base_unit']):
            # Units are compatible: convert and add
            converted = convert_units(quantity, unit, ingredient_data['base_unit'])
            if converted is not None:
                ingredient_data['total_quantity'] += converted
        else:
            # Try ingredient-specific conversion
            converted = convert_ingredient_specific(
                matching_name, 
                quantity, 
                unit, 
                ingredient_data['base_unit']
            )
            if converted is not None:
                ingredient_data['total_quantity'] += converted
    
    # Convert back to a list and prepare the result format
    aggregated_list = []
    
    for ingredient_key, data in normalized_ingredients.items():
        # Calculate fraction parts if needed
        quantity = data['total_quantity']
        is_fraction = False
        numerator = None
        denominator = None
        
        # Only convert to fractions if less than 10
        if quantity < 10 and quantity != int(quantity):
            is_fraction, numerator, denominator = decimal_to_fraction_parts(quantity)
            
        aggregated_item = {
            'name': data['display_name'],
            'normalized_name': data['normalized_name'],
            'quantity': quantity,
            'numerator': numerator if is_fraction else None,
            'denominator': denominator if is_fraction else None,
            'is_fraction': is_fraction,
            'unit': data['base_unit'],
            'original_measurements': data['measurements'],
            'multiple_forms': len(set(m['unit'] for m in data['measurements'])) > 1
        }
        
        aggregated_list.append(aggregated_item)
    
    return aggregated_list


def format_for_display(aggregated_item):
    """
    Format an aggregated item for display in the UI
    """
    display = {
        'name': aggregated_item['name'],
        'quantity_display': '',
        'unit_display': aggregated_item['unit'] or '',
        'has_multiple_forms': aggregated_item['multiple_forms'],
        'original_measurements': []
    }
    
    # Format the quantity for display
    if aggregated_item['is_fraction']:
        if int(aggregated_item['quantity']) > 0:
            # Mixed number (e.g., 1 1/2)
            whole = int(aggregated_item['quantity'])
            display['quantity_display'] = f"{whole} {aggregated_item['numerator']}/{aggregated_item['denominator']}"
        else:
            # Proper fraction (e.g., 1/2)
            display['quantity_display'] = f"{aggregated_item['numerator']}/{aggregated_item['denominator']}"
    else:
        # Decimal or whole number
        if aggregated_item['quantity'] == int(aggregated_item['quantity']):
            display['quantity_display'] = str(int(aggregated_item['quantity']))
        else:
            display['quantity_display'] = str(round(aggregated_item['quantity'], 2))
    
    # Format original measurements
    for measurement in aggregated_item['original_measurements']:
        recipe_info = f" (from {measurement['recipe_name']})" if measurement['recipe_name'] else ""
        
        # Format the quantity
        quantity = measurement['quantity']
        if quantity == int(quantity):
            quantity_str = str(int(quantity))
        else:
            quantity_str = str(round(quantity, 2))
            
        unit_str = measurement['unit'] if measurement['unit'] else ''
        
        display['original_measurements'].append({
            'text': f"{quantity_str} {unit_str}{recipe_info}".strip(),
            'recipe_id': measurement['recipe_id']
        })
    
    return display
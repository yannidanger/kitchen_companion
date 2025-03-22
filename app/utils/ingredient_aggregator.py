# app/utils/ingredient_aggregator.py
from app.utils.ingredient_normalizer import normalize_ingredient_name
from app.utils.unit_conversion import can_convert, convert_units, convert_ingredient_specific
import logging

logger = logging.getLogger(__name__)

def aggregate_ingredients_with_units(ingredients):
    """
    Advanced ingredient aggregation that maintains different unit types.
    Returns ingredients grouped by name, with quantities in original units.
    """
    aggregated = {}
    
    for ingredient in ingredients:
        name = ingredient.get('item_name', '')
        if not name:
            continue
            
        normalized_name = normalize_ingredient_name(name)
        quantity = ingredient.get('quantity')
        unit = (ingredient.get('unit') or '').lower().strip()
        
        # Create a dict entry for this ingredient if it doesn't exist
        if normalized_name not in aggregated:
            aggregated[normalized_name] = {
                'name': name,
                'normalized_name': normalized_name,
                'quantities': [],
                'id': ingredient.get('id'),
                'combined_quantity': 0,
                'primary_unit': unit  # Use first unit as primary
            }
        
        # Add this quantity/unit combination
        found = False
        for qty_entry in aggregated[normalized_name]['quantities']:
            if qty_entry['unit'] == unit:
                qty_entry['value'] += quantity
                found = True
                break
                
        if not found:
            aggregated[normalized_name]['quantities'].append({
                'value': quantity,
                'unit': unit,
                'is_fraction': ingredient.get('is_fraction', False),
                'quantity_numerator': ingredient.get('quantity_numerator'),
                'quantity_denominator': ingredient.get('quantity_denominator'),
                'source': ingredient.get('from_recipe', ''),
                'recipe_id': ingredient.get('recipe_id')
            })
        
        # Try to update combined quantity in primary unit
        if unit == aggregated[normalized_name]['primary_unit']:
            aggregated[normalized_name]['combined_quantity'] += quantity
        elif can_convert(unit, aggregated[normalized_name]['primary_unit']):
            # Units are convertible, add to combined quantity
            converted = convert_units(quantity, unit, aggregated[normalized_name]['primary_unit'])
            if converted is not None:
                aggregated[normalized_name]['combined_quantity'] += converted
    
    # Convert to list format
    result = []
    for name, data in aggregated.items():
        # Format quantities for display
        formatted_quantities = []
        for qty in data['quantities']:
            formatted_qty = format_quantity_for_display(qty)
            formatted_quantities.append(formatted_qty)
        
        # Create item for the grocery list
        item = {
            'name': data['name'],
            'id': data['id'],
            'normalized_name': data['normalized_name'],
            'quantities': formatted_quantities,
            'primary_unit': data['primary_unit'],
            'combined_quantity': data['combined_quantity'],
            'formatted_combined': format_combined_quantity(data['combined_quantity'], data['primary_unit']),
            'has_multiple_units': len(set(q['unit'] for q in data['quantities'])) > 1
        }
        result.append(item)
    
    return result

def format_quantity_for_display(quantity_data):
    """Format a quantity for display in the UI."""
    value = quantity_data['value']
    unit = quantity_data['unit']
    
    if quantity_data.get('is_fraction') and quantity_data.get('quantity_numerator') and quantity_data.get('quantity_denominator'):
        # Format fraction display
        numerator = quantity_data['quantity_numerator']
        denominator = quantity_data['quantity_denominator']
        
        if numerator >= denominator:
            whole_part = numerator // denominator
            remainder = numerator % denominator
            if remainder == 0:
                value_display = str(whole_part)
            else:
                value_display = f"{whole_part} {remainder}/{denominator}"
        else:
            value_display = f"{numerator}/{denominator}"
    else:
        # Format decimal display
        if value == int(value):
            value_display = str(int(value))
        else:
            value_display = str(value).rstrip('0').rstrip('.')
    
    return {
        'value_display': value_display,
        'unit': unit,
        'source': quantity_data.get('source', ''),
        'recipe_id': quantity_data.get('recipe_id'),
        'quantity_text': f"{value_display} {unit}".strip()
    }

def format_combined_quantity(value, unit):
    """Format the combined quantity for display."""
    if value == int(value):
        value_display = str(int(value))
    else:
        value_display = str(round(value, 2)).rstrip('0').rstrip('.')
    
    return f"{value_display} {unit}".strip()
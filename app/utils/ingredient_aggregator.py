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

def aggregate_ingredients_with_usda(ingredients):
    """
    Enhanced ingredient aggregation that leverages USDA IDs for better matching
    while maintaining backward compatibility with existing ingredients.
    Returns ingredients grouped by USDA ID or normalized name, with quantities in original units.
    """
    aggregated = {}
    
    for ingredient in ingredients:
        name = ingredient.get('item_name', '')
        # Skip empty ingredients
        if not name:
            continue
            
        # Get ingredient metadata
        quantity = ingredient.get('quantity', 0) or 0  # Handle None
        unit = (ingredient.get('unit') or '').lower().strip()
        usda_fdc_id = ingredient.get('usda_fdc_id')
        ingredient_id = ingredient.get('id') or ingredient.get('ingredient_id')
        
        # Normalize the name for matching (used when no USDA ID available)
        normalized_name = normalize_ingredient_name(name)
        
        # Create aggregation key - prefer USDA ID, then ingredient_id, then normalized name
        if usda_fdc_id:
            # USDA standardized ingredients get grouped by FDC ID
            key = f"usda_{usda_fdc_id}"
            key_type = "usda"
        elif ingredient_id:
            # Database ingredients get grouped by ingredient ID
            key = f"db_{ingredient_id}"
            key_type = "db"
        else:
            # Legacy or user-entered ingredients get grouped by normalized name and unit
            key = f"name_{normalized_name}_{unit}"
            key_type = "name"
        
        # Create a new entry for this ingredient if it doesn't exist
        if key not in aggregated:
            aggregated[key] = {
                'key': key,
                'key_type': key_type,
                'name': name,
                'normalized_name': normalized_name,
                'display_name': ingredient.get('display_name') or name,
                'id': ingredient_id,
                'usda_fdc_id': usda_fdc_id,
                'is_usda': bool(usda_fdc_id),
                'is_custom': ingredient.get('is_custom', True),
                'quantities': [],
                'primary_unit': unit,  # Use first unit as primary
                'combined_quantity': 0,
                'category': ingredient.get('category')
            }
        
        # Add this quantity/unit combination
        found = False
        for qty_entry in aggregated[key]['quantities']:
            if qty_entry['unit'] == unit:
                qty_entry['value'] += quantity
                found = True
                break
                
        if not found:
            aggregated[key]['quantities'].append({
                'value': quantity,
                'unit': unit,
                'is_fraction': ingredient.get('is_fraction', False),
                'quantity_numerator': ingredient.get('quantity_numerator'),
                'quantity_denominator': ingredient.get('quantity_denominator'),
                'source': ingredient.get('from_recipe', ''),
                'recipe_id': ingredient.get('recipe_id')
            })
        
        # Add to combined quantity in primary unit
        if unit == aggregated[key]['primary_unit']:
            aggregated[key]['combined_quantity'] += quantity
        elif can_convert(unit, aggregated[key]['primary_unit']):
            # Units are convertible, add to combined quantity
            converted = convert_units(quantity, unit, aggregated[key]['primary_unit'])
            if converted is not None:
                aggregated[key]['combined_quantity'] += converted
                
    # Format the aggregated ingredients for the grocery list
    result = format_ingredients_for_display(aggregated.values())
    return result

def format_ingredients_for_display(aggregated_ingredients):
    """Format aggregated ingredients for display in the grocery list UI"""
    result = []
    
    for item in aggregated_ingredients:
        # Format each quantity for display
        formatted_quantities = []
        for qty in item['quantities']:
            formatted_qty = format_quantity_for_display(qty)
            formatted_quantities.append(formatted_qty)
        
        # Format the combined quantity
        if item['combined_quantity'] == int(item['combined_quantity']):
            combined_value_display = str(int(item['combined_quantity']))
        else:
            combined_value_display = str(round(item['combined_quantity'], 2)).rstrip('0').rstrip('.')
        
        formatted_combined = f"{combined_value_display} {item['primary_unit']}".strip()
        
        # Create item for the grocery list
        result_item = {
            'name': item['display_name'] or item['name'],
            'id': item['id'],
            'normalized_name': item['normalized_name'],
            'usda_fdc_id': item['usda_fdc_id'],
            'is_usda': item['is_usda'],
            'is_custom': item['is_custom'],
            'quantities': formatted_quantities,
            'primary_unit': item['primary_unit'],
            'combined_quantity': item['combined_quantity'],
            'formatted_combined': formatted_combined,
            'has_multiple_units': len(set(q['unit'] for q in item['quantities'])) > 1,
            'category': item['category']
        }
        result.append(result_item)
    
    return result

def format_quantity_for_display(quantity_data):
    """Format a quantity for display in the UI"""
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
# app/utils/fraction_utils.py

import math
from fractions import Fraction

def format_fraction(value):
    """
    Formats a value as a fraction string when appropriate
    
    Args:
        value: The value to format (number or string)
        
    Returns:
        str: Formatted fraction or original value
    """
    if value is None or value == '':
        return ''
        
    # If it's already a fraction string, return it
    if isinstance(value, str) and ('/' in value or ' ' in value):
        return value
        
    # Try to convert to float
    try:
        decimal = float(value)
    except (ValueError, TypeError):
        return str(value)
        
    # If it's a whole number, return it as is
    if decimal.is_integer():
        return str(int(decimal))
        
    # Handle common fractions with a small tolerance for floating point errors
    tolerance = 0.01
    common_fractions = [
        (0.25, '1/4'),
        (0.33, '1/3'),
        (0.5, '1/2'),
        (0.66, '2/3'),
        (0.75, '3/4')
    ]
    
    for frac_decimal, frac_str in common_fractions:
        if abs(decimal - frac_decimal) < tolerance:
            return frac_str
            
    # For mixed numbers (greater than 1)
    if decimal > 1:
        whole_part = int(decimal)
        fractional_part = decimal - whole_part
        
        if fractional_part > 0:
            # Try common fractions for the fractional part
            for frac_decimal, frac_str in common_fractions:
                if abs(fractional_part - frac_decimal) < tolerance:
                    return f"{whole_part} {frac_str}"
        else:
            return str(whole_part)
            
    # If no nice fraction found, return the decimal
    return str(value)


def decimal_to_fraction_parts(decimal_value):
    """
    Convert a decimal to fraction parts (numerator/denominator)
    
    Args:
        decimal_value: Decimal number
        
    Returns:
        tuple: (is_fraction, numerator, denominator)
    """
    try:
        decimal = float(decimal_value)
    except (ValueError, TypeError):
        return False, None, None
        
    # If it's a whole number, it's not a fraction
    if decimal.is_integer():
        return False, None, None
        
    # Extract whole number part
    whole_part = int(decimal)
    fractional_part = decimal - whole_part
    
    # Handle common fractions
    tolerance = 0.01
    common_fractions = [
        (0.25, 1, 4),
        (0.33, 1, 3),
        (0.5, 1, 2),
        (0.66, 2, 3),
        (0.75, 3, 4)
    ]
    
    for frac_decimal, numerator, denominator in common_fractions:
        if abs(fractional_part - frac_decimal) < tolerance:
            return True, numerator + (whole_part * denominator), denominator
            
    # If no common fraction matches, use fractions.Fraction
    try:
        frac = Fraction(decimal).limit_denominator(8)
        return True, frac.numerator, frac.denominator
    except:
        return False, None, None


def parse_fraction(fraction_str):
    """
    Parses a fraction string to a decimal value
    
    Args:
        fraction_str: String like "1/2" or "1 1/2"
        
    Returns:
        float: Decimal value
    """
    if not fraction_str:
        return 0
        
    # Handle mixed numbers like "1 1/2"
    mixed_match = fraction_str.split()
    if len(mixed_match) == 2 and '/' in mixed_match[1]:
        whole = int(mixed_match[0])
        fraction_parts = mixed_match[1].split('/')
        numerator = int(fraction_parts[0])
        denominator = int(fraction_parts[1])
        return whole + (numerator / denominator)
        
    # Handle simple fractions like "1/2"
    if '/' in fraction_str:
        fraction_parts = fraction_str.split('/')
        numerator = int(fraction_parts[0])
        denominator = int(fraction_parts[1])
        return numerator / denominator
        
    # Handle plain numbers
    try:
        return float(fraction_str)
    except (ValueError, TypeError):
        return 0


def combine_quantities(quantities):
    """
    Combines multiple quantities, preferring fractions when possible
    
    Args:
        quantities: List of quantity values
        
    Returns:
        str: Combined quantity as a fraction or decimal
    """
    total = 0
    
    for qty in quantities:
        if isinstance(qty, str) and ('/' in qty or ' ' in qty):
            # Parse fraction string
            total += parse_fraction(qty)
        else:
            try:
                total += float(qty) if qty is not None else 0
            except (ValueError, TypeError):
                pass
                
    return format_fraction(total)
# app/utils/unit_conversion.py

class UnitGroup:
    """
    Defines a group of convertible units with conversion ratios
    """
    def __init__(self, base_unit, conversions):
        self.base_unit = base_unit  # The standard unit for this group
        self.conversions = conversions  # Dict of {unit: ratio_to_base_unit}
    
    def convert_to_base(self, quantity, unit):
        """Convert a measurement to the base unit"""
        if unit == self.base_unit:
            return quantity
        
        conversion_ratio = self.conversions.get(unit)
        if conversion_ratio is None:
            return None  # Cannot convert
        
        return quantity * conversion_ratio
    
    def convert(self, quantity, from_unit, to_unit):
        """Convert between any two units in this group"""
        if from_unit == to_unit:
            return quantity
            
        # Convert to base unit first
        base_quantity = self.convert_to_base(quantity, from_unit)
        if base_quantity is None:
            return None
        
        # Then to target unit
        if to_unit == self.base_unit:
            return base_quantity
            
        to_unit_ratio = self.conversions.get(to_unit)
        if to_unit_ratio is None:
            return None
            
        return base_quantity / to_unit_ratio


# Define common unit conversion groups
VOLUME_CONVERSIONS = UnitGroup("ml", {
    "tsp": 4.929,        # 1 tsp = 4.929 ml
    "tbsp": 14.787,      # 1 tbsp = 14.787 ml
    "fl oz": 29.574,     # 1 fl oz = 29.574 ml
    "cup": 236.588,      # 1 cup = 236.588 ml
    "pt": 473.176,       # 1 pint = 473.176 ml
    "qt": 946.353,       # 1 quart = 946.353 ml
    "gal": 3785.41,      # 1 gallon = 3785.41 ml
    "l": 1000,           # 1 liter = 1000 ml
    "ml": 1              # Base unit
})

WEIGHT_CONVERSIONS = UnitGroup("g", {
    "oz": 28.35,         # 1 oz = 28.35 g
    "lb": 453.592,       # 1 lb = 453.592 g
    "g": 1,              # Base unit
    "kg": 1000           # 1 kg = 1000 g
})

# Special case for ingredient-specific conversions
SPECIAL_INGREDIENT_CONVERSIONS = {
    "garlic": {
        "clove": {"g": 5},          # 1 clove ≈ 5g
        "bulb": {"clove": 10},      # 1 bulb ≈ 10 cloves
        "head": {"clove": 10},      # 1 head ≈ 10 cloves (same as bulb)
        "tsp": {"g": 5},            # 1 tsp minced ≈ 5g
        "tbsp": {"g": 15}           # 1 tbsp minced ≈ 15g
    },
    "basil": {
        "sprig": {"g": 2},          # 1 sprig ≈ 2g
        "bunch": {"g": 60},         # 1 bunch ≈ 60g
        "cup": {"g": 24},           # 1 cup leaves ≈ 24g
        "tbsp": {"g": 1.5}          # 1 tbsp chopped ≈ 1.5g
    },
    "onion": {
        "whole": {"cup": 1.5},      # 1 medium onion ≈ 1.5 cups chopped
        "cup": {"g": 160}           # 1 cup chopped ≈ 160g
    },
    # Add more special ingredients as needed
}

def get_conversion_group(unit):
    """Determine which conversion group a unit belongs to"""
    if unit in VOLUME_CONVERSIONS.conversions:
        return "volume"
    elif unit in WEIGHT_CONVERSIONS.conversions:
        return "weight"
    return None

def can_convert(from_unit, to_unit):
    """Check if a conversion is possible between two units"""
    from_group = get_conversion_group(from_unit)
    to_group = get_conversion_group(to_unit)
    
    # If both units belong to the same group, conversion is possible
    return from_group is not None and from_group == to_group

def convert_units(quantity, from_unit, to_unit):
    """
    Convert a quantity from one unit to another
    Returns None if conversion is not possible
    """
    from_group = get_conversion_group(from_unit)
    
    if from_group == "volume":
        return VOLUME_CONVERSIONS.convert(quantity, from_unit, to_unit)
    elif from_group == "weight":
        return WEIGHT_CONVERSIONS.convert(quantity, from_unit, to_unit)
    
    return None

def convert_ingredient_specific(ingredient, quantity, from_unit, to_unit):
    """
    Attempt an ingredient-specific conversion
    Returns None if conversion is not possible
    """
    ingredient_conversions = SPECIAL_INGREDIENT_CONVERSIONS.get(ingredient.lower())
    if not ingredient_conversions:
        return None
    
    # Check if we have a direct conversion
    from_unit_conversions = ingredient_conversions.get(from_unit)
    if from_unit_conversions and to_unit in from_unit_conversions:
        return quantity * from_unit_conversions[to_unit]
    
    # Try two-step conversion through an intermediate unit
    for intermediate_unit, conversion in from_unit_conversions.items() if from_unit_conversions else {}:
        intermediate_conversions = ingredient_conversions.get(intermediate_unit)
        if intermediate_conversions and to_unit in intermediate_conversions:
            intermediate_quantity = quantity * conversion
            return intermediate_quantity * intermediate_conversions[to_unit]
    
    return None
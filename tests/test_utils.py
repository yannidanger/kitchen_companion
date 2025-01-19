import pytest
import sys
import os
from app.utils import render_grocery_list


# Adjust Python path to locate the `app` module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils import convert_to_base_unit

def test_convert_to_base_unit():
    test_cases = [
        (2, "Tablespoon (tbsp)", 29.5736, "ml"),
        (1, "Dozen", 12, "piece"),
        (5, "Sprig", 5, "Sprig"),
        (1.5, "Cup", 360, "ml"),
        (3, "Kilogram (kg)", 3000, "grams"),
        (0.25, "Liter (l)", 250, "ml"),
        (10, "UnknownUnit", None, None),  # Should raise ValueError
    ]

    for quantity, unit, expected_quantity, expected_unit in test_cases:
        if expected_quantity is None:
            with pytest.raises(ValueError):
                convert_to_base_unit(quantity, unit)
        else:
            base_quantity, base_unit = convert_to_base_unit(quantity, unit)
            assert base_quantity == pytest.approx(expected_quantity, rel=1e-3), f"Failed for {unit}"
            assert base_unit == expected_unit, f"Failed for {unit}"

def test_render_grocery_list():
    ingredients = [
        {"item_name": "sugar", "unit": "grams", "quantity": 500},
        {"item_name": "eggs", "unit": "unitless", "quantity": 12},
        {"item_name": "milk", "unit": "ml", "quantity": 250.5},
    ]
    expected_output = (
        "500 grams of sugar\n"
        "12 unitless of eggs\n"
        "250.50 ml of milk"
    )
    result = render_grocery_list(ingredients)
    assert result == expected_output

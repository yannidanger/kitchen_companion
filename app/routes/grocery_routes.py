from flask import Blueprint, jsonify
from app.models.store_section import StoreSection
from app.models.ingredient import Ingredient
from collections import defaultdict

grocery_routes = Blueprint('grocery_routes', __name__)

@grocery_routes.route('/api/categorized_grocery_list', methods=['GET'])
def get_categorized_grocery_list():
    """Return a grocery list categorized by store sections."""
    try:
        grouped = defaultdict(list)
        ingredients = Ingredient.query.all()
        for ingredient in ingredients:
            section_name = ingredient.store_section.name if ingredient.store_section else 'Uncategorized'
            grouped[section_name].append({
                'item_name': ingredient.item_name,
                'quantity': ingredient.quantity,
                'unit': ingredient.unit
            })

        categorized_list = [{"section": section, "items": items} for section, items in grouped.items()]
        return jsonify(categorized_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

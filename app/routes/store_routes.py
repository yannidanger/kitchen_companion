from flask import Blueprint, jsonify, request
from app.models.store_section import StoreSection
from app.models.ingredient import Ingredient
from app import db

store_routes = Blueprint('store_routes', __name__)

@store_routes.route('/api/store_sections', methods=['GET'])
def get_store_sections():
    """Fetch all store sections."""
    try:
        sections = StoreSection.query.order_by(StoreSection.id).all()
        return jsonify([{'id': section.id, 'name': section.name} for section in sections])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@store_routes.route('/api/ingredients/<int:ingredient_id>/map_section', methods=['POST'])
def map_ingredient_to_section(ingredient_id):
    """Map an ingredient to a store section."""
    try:
        data = request.json
        section_id = data.get('store_section_id')
        if not section_id:
            return jsonify({'error': 'store_section_id is required'}), 400

        ingredient = Ingredient.query.get_or_404(ingredient_id)
        section = StoreSection.query.get_or_404(section_id)

        ingredient.store_section_id = section.id
        db.session.commit()
        return jsonify({'message': 'Ingredient mapped to section successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

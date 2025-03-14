from flask import Blueprint, jsonify, request
from app import db
from app.models import Store, Section, IngredientSection
from app.utils import logger
import re

store_routes = Blueprint('store_routes', __name__)




@store_routes.route('/api/stores', methods=['POST'])
def create_or_update_store():
    data = request.json
    store_id = data.get('id')
    name = data.get('name')
    sections = data.get('sections', [])

    if store_id:
        store = Store.query.get(store_id)
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        store.name = name
    else:
        store = Store(name=name)
        db.session.add(store)

    db.session.flush()  # Get the store ID for new stores

    # Update sections
    existing_section_ids = {s.id for s in store.sections}
    incoming_section_ids = {s['id'] for s in sections if 'id' in s}

    # Delete removed sections
    Section.query.filter(Section.id.in_(existing_section_ids - incoming_section_ids)).delete()

    # Add or update sections
    for idx, section_data in enumerate(sections):
        if 'id' in section_data:
            section = Section.query.get(section_data['id'])
            section.name = section_data['name']
            section.order = idx
        else:
            new_section = Section(name=section_data['name'], order=idx, store_id=store.id)
            db.session.add(new_section)

    db.session.commit()
    return jsonify({'message': 'Store saved successfully', 'store_id': store.id})

@store_routes.route('/api/stores/<int:store_id>', methods=['DELETE'])
def delete_store(store_id):
    store = Store.query.get_or_404(store_id)
    db.session.delete(store)
    db.session.commit()
    return jsonify({'message': 'Store deleted successfully'})

@store_routes.route('/api/stores', methods=['GET'])
def get_stores():
    """Get all stores."""
    try:
        stores = Store.query.all()
        store_list = []
        for store in stores:
            store_list.append({
                'id': store.id,
                'name': store.name,
                'is_default': store.is_default
            })
            
        # If no stores, create a default one
        if not store_list:
            # Check if the user_id can be null
            default_store = Store(name="My Store", is_default=True, user_id=None)
            db.session.add(default_store)
            db.session.commit()
            
            # Add a few default sections
            sections = [
                Section(name="Produce", order=0, store_id=default_store.id),
                Section(name="Dairy", order=1, store_id=default_store.id),
                Section(name="Meat", order=2, store_id=default_store.id),
                Section(name="Bakery", order=3, store_id=default_store.id),
                Section(name="Frozen", order=4, store_id=default_store.id),
                Section(name="Canned Goods", order=5, store_id=default_store.id),
                Section(name="Uncategorized", order=6, store_id=default_store.id)
            ]
            
            for section in sections:
                db.session.add(section)
            
            db.session.commit()
            
            store_list = [{
                'id': default_store.id,
                'name': default_store.name,
                'is_default': default_store.is_default
            }]
        
        return jsonify(store_list)
    except Exception as e:
        logger.error(f"Error getting stores: {e}")
        return jsonify({"error": str(e)}), 500

@store_routes.route('/api/stores/<int:store_id>/sections', methods=['GET'])
def get_store_sections(store_id):
    """Get all sections for a specific store."""
    try:
        store = Store.query.get_or_404(store_id)
        sections = Section.query.filter_by(store_id=store_id).order_by(Section.order).all()
        
        sections_list = []
        for section in sections:
            sections_list.append({
                'id': section.id,
                'name': section.name,
                'order': section.order
            })
        
        return jsonify(sections_list)
    except Exception as e:
        logger.error(f"Error getting sections for store {store_id}: {e}")
        return jsonify({"error": str(e)}), 500

@store_routes.route('/api/ingredient_sections', methods=['GET'])
def get_ingredient_sections():
    """Get ingredient-section mappings for a store."""
    try:
        store_id = request.args.get('store_id')
        if not store_id:
            return jsonify({"error": "Store ID is required"}), 400
            
        mappings = IngredientSection.query.join(Section).filter(Section.store_id == store_id).all()
        
        result = []
        for mapping in mappings:
            result.append({
                'ingredient_id': mapping.ingredient_id,
                'section_id': mapping.section_id,
                'order': mapping.order
            })
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting ingredient sections: {e}")
        return jsonify({"error": str(e)}), 500

@store_routes.route('/api/save_ingredient_sections', methods=['POST'])
def save_ingredient_sections():
    """Save ingredient-section mappings and section data."""
    try:
        data = request.json
        if not data or 'store_id' not in data or 'sections' not in data:
            return jsonify({"error": "Store ID and section data are required"}), 400
            
        store_id = data['store_id']
        sections_data = data['sections']
        
        # Get all section IDs for this store
        store_section_ids = [section.id for section in Section.query.filter_by(store_id=store_id).all()]
        
        # Get the store
        store = Store.query.get_or_404(store_id)
        
        # Find existing uncategorized section or create one
        uncategorized_section = Section.query.filter_by(
            store_id=store_id, 
            name="Uncategorized"
        ).first()
        
        if not uncategorized_section:
            uncategorized_section = Section(
                name="Uncategorized", 
                store_id=store_id, 
                order=999
            )
            db.session.add(uncategorized_section)
            db.session.flush()
            
        # Clear all existing mappings for this store's sections
        if store_section_ids:
            IngredientSection.query.filter(
                IngredientSection.section_id.in_(store_section_ids)
            ).delete(synchronize_session=False)
        
        # Track processed section names to avoid duplicates (use lowercase for case-insensitive comparison)
        processed_section_names = {"uncategorized"}
        
        # Process regular sections
        for section_data in sections_data:
            # Sanitize and standardize section name
            section_name = section_data.get('name', '').strip()
            
            # Standardize the section name: Title case with proper spacing
            # Replace multiple spaces with a single space
            section_name = re.sub(r'\s+', ' ', section_name)
            
            # Apply title case, but preserve common abbreviations
            section_name = section_name.title()
            
            # Skip empty sections
            if not section_name:
                continue
                
            section_id = section_data.get('id')
            ingredients = section_data.get('ingredients', [])
            
            # Skip empty temporary sections
            if not ingredients and section_id and str(section_id).startswith('temp-'):
                continue
                
            # Skip duplicate section names (case-insensitive)
            if section_name.lower() in processed_section_names:
                continue
                
            processed_section_names.add(section_name.lower())
                
            # Skip uncategorized - we'll handle it separately
            if section_name.lower() == "uncategorized":
                section = uncategorized_section
            else:
                # Create or update regular section
                if section_id and not str(section_id).startswith('temp-'):
                    section = Section.query.get(section_id)
                    if section:
                        section.name = section_name  # Use standardized name
                    else:
                        section = Section(name=section_name, store_id=store_id, order=0)
                        db.session.add(section)
                        db.session.flush()
                else:
                    # Create a new section
                    section = Section(name=section_name, store_id=store_id, order=0)
                    db.session.add(section)
                    db.session.flush()
            
            # Add ingredient mappings
            for i, ingredient_data in enumerate(ingredients):
                ingredient_id = ingredient_data.get('id')
                
                if not ingredient_id:
                    continue
                    
                mapping = IngredientSection(
                    ingredient_id=ingredient_id,
                    section_id=section.id,
                    order=i
                )
                db.session.add(mapping)
        
        db.session.commit()
        return jsonify({"message": "Ingredient sections saved successfully"})
        
    except Exception as e:
        logger.error(f"Error saving ingredient sections: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@store_routes.route('/api/stores/<int:store_id>/sections/reorder', methods=['POST'])
def reorder_sections(store_id):
    """Reorder sections within a store."""
    try:
        data = request.json
        if not data or 'sections' not in data:
            return jsonify({"error": "Section order data is required"}), 400
            
        section_order = data['sections']
        
        # Update section orders
        for idx, section_id in enumerate(section_order):
            section = Section.query.get(section_id)
            if section and section.store_id == store_id:
                section.order = idx
                
        db.session.commit()
        return jsonify({"message": "Sections reordered successfully"})
        
    except Exception as e:
        logger.error(f"Error reordering sections: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@store_routes.route('/api/stores/<int:store_id>/set-default', methods=['POST'])
def set_default_store(store_id):
    try:
        # Clear default flag from all stores first
        Store.query.update({Store.is_default: False})
        
        # Set the requested store as default
        store = Store.query.get(store_id)
        if not store:
            return jsonify({"error": "Store not found"}), 404
            
        store.is_default = True
        db.session.commit()
        
        return jsonify({"success": True, "message": f"{store.name} set as default store"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
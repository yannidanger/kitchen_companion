from flask import Blueprint, jsonify, request
from app import db
from app.models import Store, Section
from app.utils import logger

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
from app.models.store_section import StoreSection
from app import db

def populate_default_store_sections():
    """Seed the database with default store sections."""
    default_sections = [
        "Pharmacy Section", "Bakery Section", "Deli", "Produce Section", "Dairy Section",
        "Aisle 1: Breakfast Items", "Aisle 2: Baby Products", "Aisle 3: Health & Beauty",
        "Aisle 4: Soup", "Aisle 5: Ethnic Foods", "Aisle 6: Candy",
        "Aisle 7: Condiments & Baking", "Aisle 8: Canned, Dry, Sauces",
        "Aisle 9: Pet Supplies, Magazines, Batteries", "Aisle 10: Cleaning Supplies",
        "Aisle 11: Paper Goods", "Aisle 12: Bread, Water & Snacks",
        "Aisle 13: Frozen Foods Section", "Seafood Section", "Meat Section",
        "Aisle 14: Cheeses, Hotdogs, Frozen Meals", "Aisle 15: Dessert Aisle",
        "Alcohol Section"
    ]
    for section_name in default_sections:
        if not StoreSection.query.filter_by(name=section_name).first():
            db.session.add(StoreSection(name=section_name))
    db.session.commit()

from app import db

class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    store_section_id = db.Column(db.Integer, db.ForeignKey('store_section.id'), nullable=True)
    # Other fields remain the same

from app import db

class StoreSection(db.Model):
    __tablename__ = 'store_section'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)

    # Relationships
    ingredients = db.relationship(
        'Ingredient',
        backref='store_section',
        lazy=True,
        cascade='all, delete-orphan'
    )

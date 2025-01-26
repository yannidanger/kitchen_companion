from flask_sqlalchemy import SQLAlchemy
from app import db
from datetime import datetime


db = SQLAlchemy()

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cook_time = db.Column(db.Integer, nullable=True)
    servings = db.Column(db.Integer, nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    ingredients = db.relationship(
        'Ingredient', backref='recipe', lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cook_time': self.cook_time,
            'servings': self.servings,
            'instructions': self.instructions,
            'ingredients': [ingredient.to_dict() for ingredient in self.ingredients],
        }


from fractions import Fraction

class Ingredient(db.Model):
    __tablename__ = 'ingredient'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=True)  # Allows NULL values
    original_quantity = db.Column(db.String(50), nullable=True)  # Stores the original input
    unit = db.Column(db.String(50), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    descriptor = db.Column(db.String(100), nullable=True)
    additional_descriptor = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        """Convert the Ingredient object into a dictionary."""
        return {
        'id': self.id,
        'recipe_id': self.recipe_id,
        'item_name': self.item_name,
        'quantity': self.original_quantity,
        'unit': self.unit,
        'size': self.size,
        'descriptor': self.descriptor,  # Return raw descriptor
        'additional_descriptor': self.additional_descriptor  # Return raw additional descriptor
    }
class Food(db.Model):
    __tablename__ = 'food'

    fdc_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)

class MeasureUnit(db.Model):
    __tablename__ = 'measure_unit'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class WeeklyPlan(db.Model):
    __tablename__ = 'weekly_plan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    meals = db.relationship('MealSlot', backref='weekly_plan', lazy=True, cascade="all, delete-orphan")

    @property
    def ingredient_count(self):
        ingredients = set()
        for meal in self.meals:
            if meal.recipe_id:
                recipe = Recipe.query.get(meal.recipe_id)
                if recipe:
                    for ingredient in recipe.ingredients:
                        ingredients.add(ingredient.item_name)
        return len(ingredients)

class MealSlot(db.Model):
    __tablename__ = 'meal_slot'

    id = db.Column(db.Integer, primary_key=True)
    weekly_plan_id = db.Column(db.Integer, db.ForeignKey('weekly_plan.id'), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # e.g., "breakfast", "lunch", "dinner"
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'day': self.day,
            'meal_type': self.meal_type,
            'recipe_id': self.recipe_id,
        }
    
class Store(db.Model):
    __tablename__ = 'store'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    sections = db.relationship('Section', backref='store', cascade='all, delete-orphan', lazy=True)


class Section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, nullable=False)  # For custom ordering
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)


class IngredientSection(db.Model):
    __tablename__ = 'ingredient_section'
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)  # Use 'ingredient'
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)  # Already correct

    # Define the relationship
    section = db.relationship('Section', backref='ingredient_sections', lazy=True)
    ingredient = db.relationship('Ingredient', backref='ingredient_sections', lazy=True)



class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    stores = db.relationship('Store', backref='user', lazy=True)

class StoreSection(db.Model):
    __tablename__ = "store_sections"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    order = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<StoreSection(name={self.name}, order={self.order})>"


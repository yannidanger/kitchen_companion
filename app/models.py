from flask_sqlalchemy import SQLAlchemy
from app import db
from datetime import datetime


db = SQLAlchemy()


from fractions import Fraction

class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}
    
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

from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship

class RecipeComponent(db.Model):
    __tablename__ = 'recipe_component'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    sub_recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    parent_recipe = db.relationship(
        "Recipe",
        foreign_keys=[recipe_id],
        back_populates="components"
    )

    sub_recipe = db.relationship(
        "Recipe",
        foreign_keys=[sub_recipe_id],
        back_populates="used_in_recipes"
    )

    def to_dict(self, depth=1):
        """
        Convert recipe component object to dictionary, preventing infinite recursion.
        :param depth: Controls how deep the nesting should go.
        """
        if depth <= 0:
            return {'id': self.id}  # Return minimal data to prevent recursion

        return {
            'id': self.id,
            'sub_recipe': self.sub_recipe.to_dict(depth - 1) if self.sub_recipe else None,
            'quantity': self.quantity
        }





class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredient'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(50))

    # ✅ Ensure RecipeIngredient is linked back to Recipe
    recipe = db.relationship("Recipe", back_populates="ingredients")
    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        return {
            'id': self.id,
            'ingredient': self.ingredient.to_dict(),
            'quantity': self.quantity,
            'unit': self.unit
        }

    

class Recipe(db.Model):
    __tablename__ = 'recipe'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    cook_time = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    instructions = db.Column(db.Text)

    components = db.relationship(
        "RecipeComponent",
        foreign_keys="[RecipeComponent.recipe_id]",
        back_populates="parent_recipe",
        cascade="all, delete-orphan"
    )

    used_in_recipes = db.relationship(
        "RecipeComponent",
        foreign_keys="[RecipeComponent.sub_recipe_id]",
        back_populates="sub_recipe",
        cascade="all, delete-orphan"
    )

    ingredients = db.relationship("RecipeIngredient", back_populates="recipe")

    def to_dict(self, depth=1):
        """
        Convert recipe object to dictionary, preventing infinite recursion.
        :param depth: Controls how deep the nesting should go.
        """
        if depth <= 0:
            return {'id': self.id, 'name': self.name}  # Return minimal data to prevent recursion

        return {
            'id': self.id,
            'name': self.name,
            'cook_time': self.cook_time,
            'servings': self.servings,
            'instructions': self.instructions,
            'ingredients': [ri.to_dict() for ri in self.ingredients],
            'components': [component.to_dict(depth - 1) for component in self.components],
            'used_in_recipes': [component.to_dict(depth - 1) for component in self.used_in_recipes]
        }




from app import db
from datetime import datetime

class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # ADD THIS RELATIONSHIP HERE:
    ingredient_recipes = db.relationship(
        "RecipeIngredient",
        back_populates="ingredient",
        cascade="all, delete-orphan"
    )

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
                        # Change this line:
                        # from: ingredients.add(ingredient.item_name)
                        # to:
                        if ingredient.ingredient:
                            ingredients.add(ingredient.ingredient.name)
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
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    order = db.Column(db.Integer, default=0)  # Add this field for custom ordering

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
        return {
            'id': self.id,
            'quantity': self.quantity,
            'sub_recipe': self.sub_recipe.to_dict(depth - 1) if self.sub_recipe and depth > 0 else {'id': self.sub_recipe_id}
        }



class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredient'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=True)
    sub_recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=True)
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(50))
    size = db.Column(db.String(50))  # Add this line if not already there
    descriptor = db.Column(db.String(100))  # Add this line if not already there
    additional_descriptor = db.Column(db.String(100))  # Add this line if not already there
    quantity_numerator = db.Column(db.Integer)
    quantity_denominator = db.Column(db.Integer)
    is_fraction = db.Column(db.Boolean, default=False)

    # Relationships (clearly specify foreign keys)
    recipe = db.relationship(
        "Recipe",
        foreign_keys=[recipe_id],
        back_populates="ingredients"
    )
    sub_recipe = db.relationship(
        "Recipe",
        foreign_keys=[sub_recipe_id],
        back_populates="used_as_sub_recipe"
    )
    ingredient = db.relationship("Ingredient", back_populates="ingredient_recipes")

    def to_dict(self):
        fraction_str = None
        if self.is_fraction and self.quantity_numerator is not None and self.quantity_denominator is not None:
            if self.quantity_numerator >= self.quantity_denominator:
                whole_part = self.quantity_numerator // self.quantity_denominator
                numerator = self.quantity_numerator % self.quantity_denominator
                if numerator == 0:
                    fraction_str = str(whole_part)
                else:
                    fraction_str = f"{whole_part} {numerator}/{self.quantity_denominator}"
            else:
                fraction_str = f"{self.quantity_numerator}/{self.quantity_denominator}"
                
        return {
            'id': self.id,
            'ingredient': self.ingredient.to_dict() if self.ingredient else None,
            'sub_recipe': self.sub_recipe.to_dict() if self.sub_recipe else None,
            'quantity': self.quantity,
            'unit': self.unit,
            'size': self.size,
            'descriptor': self.descriptor,
            'additional_descriptor': self.additional_descriptor,
            'is_fraction': self.is_fraction,
            'quantity_numerator': self.quantity_numerator,
            'quantity_denominator': self.quantity_denominator,
            'fraction_str': fraction_str
        }

class Recipe(db.Model):
    __tablename__ = 'recipe'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    cook_time = db.Column(db.String(100))
    servings = db.Column(db.Integer)
    instructions = db.Column(db.Text)
    favorite = db.Column(db.Boolean, default=False)

    ingredients = db.relationship(
        "RecipeIngredient",
        foreign_keys='RecipeIngredient.recipe_id',
        back_populates="recipe",
        cascade="all, delete-orphan"
    )

    used_as_sub_recipe = db.relationship(
        "RecipeIngredient",
        foreign_keys='RecipeIngredient.sub_recipe_id',
        back_populates="sub_recipe"
    )

    components = db.relationship(
        "RecipeComponent",
        foreign_keys='RecipeComponent.recipe_id',
        back_populates="parent_recipe",
        cascade="all, delete-orphan"
    )

    used_in_recipes = db.relationship(
        "RecipeComponent",
        foreign_keys='RecipeComponent.sub_recipe_id',
        back_populates="sub_recipe",
        cascade="all, delete-orphan"
    )
    
    meal_slots = db.relationship(
    "MealSlot",
    backref="recipe",
    cascade="all, delete-orphan",
    lazy=True
)

    def to_dict(self, depth=1):
        """Convert recipe to dictionary, with control over sub-recipe expansion depth."""
        result = {
            'id': self.id,
            'name': self.name,
            'cook_time': self.cook_time,
            'servings': self.servings,
            'instructions': self.instructions,
            'ingredients': [ri.to_dict() for ri in self.ingredients],
        }
        
        # Only include components if we're still within the depth limit
        if depth > 0:
            result['components'] = [
                {
                    'id': component.id,
                    'quantity': component.quantity,
                    'sub_recipe': component.sub_recipe.to_dict(depth - 1) if component.sub_recipe else None
                }
                for component in self.components
            ]
        else:
            # Just include basic component info at max depth
            result['components'] = [
                {
                    'id': component.id,
                    'quantity': component.quantity,
                    'sub_recipe': {'id': component.sub_recipe_id, 'name': component.sub_recipe.name} if component.sub_recipe else None
                }
                for component in self.components
            ]
        
        return result









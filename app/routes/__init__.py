from flask import Blueprint
from .recipes import recipes_routes
from .ingredients import ingredient_routes
from .stores import store_routes
from .grocery import grocery_routes, generate_grocery_bp  # Add generate_grocery_bp here
from .meal_planner import meal_planner_routes
from .sub_recipes import sub_recipes_bp
from .usda_routes import usda_bp

__all__ = [
    'recipes_routes',
    'meal_planner_routes',
    'store_routes',
    'ingredient_routes',
    'grocery_routes',
    'sub_recipes_bp',
    'generate_grocery_bp',
    'usda_bp'
]

def register_routes(app):
    app.register_blueprint(recipes_routes, url_prefix="/api/recipes")
    app.register_blueprint(ingredient_routes, url_prefix="/api/ingredients")
    app.register_blueprint(store_routes, url_prefix="/api/stores")
    app.register_blueprint(grocery_routes, url_prefix="/api/grocery_list")
    app.register_blueprint(meal_planner_routes, url_prefix="/api/weekly_plan")
    app.register_blueprint(sub_recipes_bp, url_prefix="/api/sub_recipes")
    app.register_blueprint(usda_bp, url_prefix="/api/usda")  # Add this line
    app.register_blueprint(generate_grocery_bp)  # Add this line
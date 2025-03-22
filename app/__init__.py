# __init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from flask_cors import CORS

# Initialize extensions globally
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # Absolute paths for templates and static files
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

    # Initialize the Flask app
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)
    CORS(app)
    # Database configuration
    from config import Config
    app.config.from_object(Config)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes import recipes_routes
    app.register_blueprint(recipes_routes)
    from app.routes import meal_planner_routes
    app.register_blueprint(meal_planner_routes)
    from app.routes import store_routes
    app.register_blueprint(store_routes)
    from app.routes import ingredient_routes
    app.register_blueprint(ingredient_routes)
    from app.routes import grocery_routes
    app.register_blueprint(grocery_routes)
    from app.routes import sub_recipes_bp
    app.register_blueprint(sub_recipes_bp)
    from app.routes import generate_grocery_bp
    app.register_blueprint(generate_grocery_bp)
    
    # Add USDA blueprint
    from app.routes import usda_bp
    app.register_blueprint(usda_bp)
    
    return app
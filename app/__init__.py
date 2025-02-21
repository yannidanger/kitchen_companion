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
    app.register_blueprint(store_routes, url_prefix='/stores')  # Adjust the URL prefix if needed
    from app.routes import ingredient_routes
    app.register_blueprint(ingredient_routes, url_prefix='/ingredients')
    from app.routes import grocery_routes
    app.register_blueprint(grocery_routes, url_prefix='/grocery')
    from app.routes import sub_recipes_bp
    print("Registering sub_recipes_bp...")
    app.register_blueprint(sub_recipes_bp)
    print("sub_recipes_bp registered successfully.")


    return app

# Ensure 'db' is importable
from app.models import *
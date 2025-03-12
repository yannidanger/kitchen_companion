from flask import Blueprint, jsonify, request
from app import db
from app.models import Recipe, RecipeComponent
import logging

sub_recipes_bp = Blueprint('sub_recipes', __name__)

# Configure logging
logger = logging.getLogger(__name__)

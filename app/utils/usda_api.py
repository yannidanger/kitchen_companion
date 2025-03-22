# app/utils/usda_api.py
import requests
import os
import logging

logger = logging.getLogger(__name__)

# Try to get API key from config
def get_api_key():
    try:
        from flask import current_app
        return current_app.config.get('USDA_API_KEY')
    except (ImportError, RuntimeError):
        return os.environ.get('USDA_API_KEY')

BASE_URL = 'https://api.nal.usda.gov/fdc/v1'

def search_foods(query, page_size=25, page_number=1):
    """Search USDA FoodData Central for foods matching the query"""
    api_key = get_api_key()
    if not api_key:
        logger.error("USDA API key not found. Set USDA_API_KEY environment variable.")
        return {'error': "API key not configured"}
    
    url = f"{BASE_URL}/foods/search"
    params = {
        'api_key': api_key,
        'query': query,
        'pageSize': page_size,
        'pageNumber': page_number,
        'dataType': ['Foundation', 'SR Legacy', 'Survey (FNDDS)']
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"USDA API request failed: {e}")
        return {'error': f"API request failed: {str(e)}"}

def get_food_details(fdc_id):
    """Get detailed information about a specific food item"""
    api_key = get_api_key()
    if not api_key:
        logger.error("USDA API key not found. Set USDA_API_KEY environment variable.")
        return {'error': "API key not configured"}
    
    url = f"{BASE_URL}/food/{fdc_id}"
    params = {
        'api_key': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"USDA API request failed: {e}")
        return {'error': f"API request failed: {str(e)}"}

def extract_food_category(food_data):
    """Extract food category from USDA food data"""
    # Different data types store category information differently
    if 'foodCategory' in food_data:
        return food_data['foodCategory']
    elif 'foodCategoryLabel' in food_data:
        return food_data['foodCategoryLabel']
    elif 'foodGroup' in food_data:
        return food_data['foodGroup']
    
    return None

def simplify_food_data(food):
    """Convert USDA food data to simplified format for frontend"""
    return {
        'fdc_id': food.get('fdcId'),
        'description': food.get('description', ''),
        'brand_owner': food.get('brandOwner', ''),
        'ingredients': food.get('ingredients', ''),
        'data_type': food.get('dataType', ''),
        'category': extract_food_category(food)
    }
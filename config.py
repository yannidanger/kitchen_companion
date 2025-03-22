# config.py
import os

class Config:
    SECRET_KEY = "your-secret-key"
    SQLALCHEMY_DATABASE_URI = "postgresql://kitchen_user:samanthamew@localhost/kitchenapp"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USDA_API_KEY = os.environ.get('USDA_API_KEY', 'Zb6YfdLlwpStImwNarucwnCq3JKqm1ugLCBWDGTI')  # Add this line
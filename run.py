# run.py
from app import create_app

# Create the Flask app instance
app = create_app()

with app.app_context():
    print(app.url_map)

if __name__ == '__main__':
    # Run the app with debug mode enabled, accessible from all interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)

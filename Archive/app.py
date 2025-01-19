import sqlite3
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

def get_db_connection():
    return sqlite3.connect('G:/GroceriesProject/Kitchenapp/SQLiteStuff/usda_data.db')

def add_recipe_to_database(name, instructions, ingredients):
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()

            # Insert recipe
            cursor.execute("INSERT INTO recipes (name, instructions) VALUES (?, ?)", (name, instructions))
            recipe_id = cursor.lastrowid

            # Insert ingredients
            for ingredient in ingredients:
                cursor.execute(
                    "INSERT INTO ingredients (recipe_id, food_name, quantity, unit, size, descriptor, additional_descriptor) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (recipe_id, ingredient['food_name'], ingredient['quantity'], ingredient['unit'],
                     ingredient['size'], ingredient['descriptor'], ingredient['additional_descriptor'])
                )
    except sqlite3.Error as e:
        print(f"Database error: {e}")


@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """
    Fetch all recipes from the database and return them as JSON.
    """
    try:
        conn = sqlite3.connect("G:/GroceriesProject/Kitchenapp/SQLiteStuff/usda_data.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch all recipes
        cursor.execute("SELECT id, name FROM recipes ORDER BY name")
        recipes = cursor.fetchall()

        # Convert rows to dictionaries
        recipe_list = [{"id": recipe["id"], "name": recipe["name"]} for recipe in recipes]

        conn.close()
        return jsonify({"success": True, "recipes": recipe_list}), 200

    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/recipe/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """
    Fetch a single recipe by ID.
    """
    try:
        conn = sqlite3.connect("G:/GroceriesProject/Kitchenapp/SQLiteStuff/usda_data.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch the recipe
        cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        recipe = cursor.fetchone()

        if recipe:
            # Fetch recipe ingredients
            cursor.execute(
                "SELECT r.food_id, f.description, r.quantity, u.name AS unit "
                "FROM recipe_ingredients r "
                "LEFT JOIN food f ON r.food_id = f.fdc_id "
                "LEFT JOIN measure_unit u ON r.unit_id = u.id "
                "WHERE r.recipe_id = ?",
                (recipe_id,)
            )
            ingredients = cursor.fetchall()

            recipe_details = {
                "id": recipe["id"],
                "name": recipe["name"],
                "instructions": recipe["instructions"],
                "ingredients": [
                    {
                        "food_id": ing["food_id"],
                        "description": ing["description"],
                        "quantity": ing["quantity"],
                        "unit": ing["unit"],
                    }
                    for ing in ingredients
                ],
            }

            conn.close()
            return jsonify({"success": True, "recipe": recipe_details}), 200
        else:
            conn.close()
            return jsonify({"success": False, "error": "Recipe not found"}), 404

    except Exception as e:
        print(f"Error fetching recipe: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/recipe', methods=['POST'])
def add_recipe():
    """
    Add a new recipe with structured ingredients to the database.
    """
    try:
        data = request.json
        name = data['name']
        instructions = data['instructions']
        ingredients = data['ingredients']

        # Use a fresh connection for this request
        conn = sqlite3.connect("G:/GroceriesProject/Kitchenapp/SQLiteStuff/usda_data.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Insert the recipe
        cursor.execute("INSERT INTO recipes (name, instructions) VALUES (?, ?)", (name, instructions))
        recipe_id = cursor.lastrowid
        print(f"Inserted recipe with ID: {recipe_id}")

        # Insert ingredients
        for ingredient in ingredients:
            food_name = ingredient['food_name']
            quantity = ingredient.get('quantity', None)
            unit = ingredient.get('unit', None)

            # Check or insert food
            print(f"Checking if food exists for: {food_name}")
            cursor.execute("SELECT fdc_id FROM food WHERE description = ?", (food_name,))
            food_row = cursor.fetchone()

            if not food_row:
                print(f"Inserting new food: {food_name}")
                cursor.execute(
                    "INSERT INTO food (description, data_type, food_category_id, publication_date) VALUES (?, ?, ?, ?)",
                    (food_name, None, None, None)
                )
                conn.commit()  # Commit the transaction to finalize the insert
                food_id = cursor.lastrowid
                print(f"New food ID for {food_name}: {food_id}")
            else:
                food_id = food_row["fdc_id"]

            print(f"Food ID for {food_name}: {food_id}")

            # Skip adding this ingredient if food_id is still None
            if food_id is None:
                print(f"Skipping ingredient '{food_name}' due to missing food_id.")
                continue

            # Check or insert unit
            if unit:
                print(f"Checking if measure unit exists: {unit}")
                cursor.execute("SELECT id FROM measure_unit WHERE name = ?", (unit,))
                unit_row = cursor.fetchone()
                if not unit_row:
                    print(f"Inserting new measure unit: {unit}")
                    cursor.execute("INSERT INTO measure_unit (name) VALUES (?)", (unit,))
                    unit_id = cursor.lastrowid
                else:
                    unit_id = unit_row["id"]
            else:
                unit_id = None

            # Insert recipe ingredient
            print(f"Adding ingredient: {food_name}, Quantity: {quantity}, Unit: {unit}")
            cursor.execute(
                "INSERT INTO recipe_ingredients (recipe_id, food_id, quantity) VALUES (?, ?, ?)",
                (recipe_id, food_id, quantity or None)
            )

        conn.commit()  # Commit all changes
        conn.close()

        return jsonify({"success": True}), 200

    except Exception as e:
        app.logger.error(f"Error adding recipe: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/recipe/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    data = request.json
    name = data['name']
    ingredients = ', '.join(data['ingredients'])
    instructions = data['instructions']

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE recipes SET name = ?, ingredients = ?, instructions = ? WHERE id = ?",
            (name, ingredients, instructions, recipe_id)
        )
    return jsonify({"message": "Recipe updated successfully"}), 200

@app.route('/api/recipe/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    return jsonify({"message": "Recipe deleted successfully"}), 200

@app.route('/save-weekly-plan', methods=['POST'])
def save_weekly_plan():
    try:
        plan_data = request.json
        if not plan_data:
            return jsonify({"success": False, "error": "No data received"}), 400

        conn = get_db_connection()
        conn.execute('DELETE FROM weekly_plan')
        conn.commit()

        for entry in plan_data:
            for meal, recipe_id in entry.items():
                if recipe_id and meal in ['breakfast', 'lunch', 'dinner']:
                    conn.execute(
                        'INSERT INTO weekly_plan (meal_type, recipe_id) VALUES (?, ?)',
                        (meal, recipe_id)
                    )
        print("Saving to weekly_plan:", plan_data)

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200
    except Exception as e:
        app.logger.error(f"Error saving weekly plan: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


        return jsonify({"success": True}), 200
    except Exception as e:
        app.logger.error(f"Error saving weekly plan: {e}")
        print("Weekly Plan Data:", plan_data)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/planner', methods=['GET'])
def weekly_planner():
    """
    Render the weekly planner and populate recipes dynamically.
    """
    with get_db_connection() as conn:
        recipes = conn.execute("SELECT id, name FROM recipes").fetchall()
    return render_template('index.html', recipes=recipes)


@app.route('/recipes.html')
def recipes_page():
    """
    Render the Recipe Management page.
    """
    return render_template('recipes.html')

@app.route('/generate-shopping-list', methods=['POST'])
def generate_grocery_list():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
            SELECT f.description AS name,
                   CASE WHEN fp.amount IS NOT NULL AND mu.name IS NOT NULL 
                        THEN '(' || fp.amount || ' ' || mu.name || ')'
                        ELSE 'None'
                   END AS shoppable_quantity,
                   SUM(ri.quantity) AS needed_quantity
            FROM weekly_plan AS wp
            JOIN recipe_ingredients AS ri ON wp.recipe_id = ri.recipe_id
            JOIN food AS f ON ri.food_id = f.fdc_id
            LEFT JOIN food_portion AS fp ON f.fdc_id = fp.fdc_id
            LEFT JOIN measure_unit AS mu ON fp.measure_unit_id = mu.id
            WHERE ri.quantity > 0.0
            GROUP BY f.description, fp.amount, mu.name
            """
            results = cursor.execute(query).fetchall()

            grocery_list = [
                {
                    "name": row[0],
                    "shoppable_quantity": row[1] if row[1] != "None" else None,
                    "needed_quantity": row[2],
                }
                for row in results
            ]

        return jsonify(grocery_list), 200

    except Exception as e:
        app.logger.error(f"Error generating grocery list: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/test_db')
def test_db():
    """
    Test the database connection and list available tables.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        return jsonify({"tables": tables}), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    """
    Render the main page with the weekly planner and buttons.
    """
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)

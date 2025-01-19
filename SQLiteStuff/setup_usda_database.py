import os
import sqlite3
import pandas as pd

DB_PATH = "usda_data.db"
CSV_DIR = "G:\GroceriesProject\Kitchenapp\SQLiteStuff"

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def create_tables():
    """Create tables for the USDA database."""
    tables = {
        "food": """
            CREATE TABLE IF NOT EXISTS food (
                fdc_id INTEGER PRIMARY KEY,
                data_type TEXT,
                description TEXT,
                food_category_id REAL,
                publication_date TEXT
            );
        """,
        "food_portion": """
            CREATE TABLE IF NOT EXISTS food_portion (
                id INTEGER PRIMARY KEY,
                fdc_id INTEGER,
                seq_num REAL,
                amount REAL,
                measure_unit_id INTEGER,
                portion_description TEXT,
                modifier TEXT,
                gram_weight REAL,
                data_points REAL,
                footnote REAL,
                min_year_acquired REAL
            );
        """,
        "measure_unit": """
            CREATE TABLE IF NOT EXISTS measure_unit (
                id INTEGER PRIMARY KEY,
                name TEXT
            );
        """,
        "recipes": """
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
        """,
        "recipe_ingredients": """
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                food_id INTEGER,
                quantity REAL
            );
        """,
        "weekly_plan": """
            CREATE TABLE IF NOT EXISTS weekly_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL
            );
        """
    }
    for table_name, ddl in tables.items():
        cursor.execute(ddl)
    conn.commit()

def load_csv_to_table(csv_name, table_name):
    """Load data from a CSV file into a table."""
    csv_path = os.path.join(CSV_DIR, csv_name)
    try:
        data = pd.read_csv(csv_path)
        data.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Loaded data for table: {table_name}")
    except FileNotFoundError:
        print(f"CSV file not found: {csv_name}")
    except Exception as e:
        print(f"Error loading {csv_name}: {e}")

def add_default_food_portions():
    """Ensure all food IDs in recipe_ingredients are in food_portion."""
    cursor.execute("""
        SELECT DISTINCT ri.food_id 
        FROM recipe_ingredients AS ri
        LEFT JOIN food_portion AS fp ON ri.food_id = fp.fdc_id
        WHERE fp.fdc_id IS NULL;
    """)
    missing_foods = cursor.fetchall()
    if missing_foods:
        print(f"Adding missing food_portion entries for: {missing_foods}")
        default_entries = [
            (food_id[0], 1, 1.0, 1001, 30.0) for food_id in missing_foods
        ]
        cursor.executemany("""
            INSERT INTO food_portion (fdc_id, seq_num, amount, measure_unit_id, gram_weight)
            VALUES (?, ?, ?, ?, ?)
        """, default_entries)
        conn.commit()

def add_test_data():
    """Add sample test data to recipes, weekly_plan, and recipe_ingredients."""
    # Add recipes
    cursor.executemany(
        "INSERT INTO recipes (name) VALUES (?)",
        [("Recipe 1",), ("Recipe 2",)]
    )
    # Add weekly plan
    cursor.executemany(
        "INSERT INTO weekly_plan (recipe_id) VALUES (?)",
        [(1,), (2,)]
    )
    # Add recipe ingredients
    cursor.executemany(
        "INSERT INTO recipe_ingredients (recipe_id, food_id, quantity) VALUES (?, ?, ?)",
        [
            (1, 319874, 2.5),  # Hummus, Sabra Classic
            (1, 330417, 2.5),  # Oil, coconut
            (2, 321363, 3.0)   # Salt
        ]
    )
    conn.commit()

def main():
    create_tables()
    load_csv_to_table("food.csv", "food")
    load_csv_to_table("food_portion.csv", "food_portion")
    load_csv_to_table("measure_unit.csv", "measure_unit")
    add_test_data()
    add_default_food_portions()
    print("Database setup complete!")

if __name__ == "__main__":
    main()

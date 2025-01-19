import sqlite3

def test_food_insertion():
    conn = sqlite3.connect("G:/GroceriesProject/Kitchenapp/SQLiteStuff/usda_data.db")
    cursor = conn.cursor()

    try:
        # Check if food exists
        food_name = "egg"
        cursor.execute("SELECT fdc_id FROM food WHERE description = ?", (food_name,))
        food_row = cursor.fetchone()

        if food_row:
            print(f"Food already exists. Food ID: {food_row[0]}")
        else:
            # Insert new food
            print(f"Inserting new food: {food_name}")
            cursor.execute(
                "INSERT INTO food (description, data_type, food_category_id, publication_date) VALUES (?, ?, ?, ?)",
                (food_name, None, None, None)
            )
            conn.commit()
            food_id = cursor.lastrowid
            print(f"New food ID: {food_id}")

    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()

test_food_insertion()

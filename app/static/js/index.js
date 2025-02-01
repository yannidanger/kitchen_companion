document.addEventListener('DOMContentLoaded', () => {
    const groceryListContainer = document.getElementById('grocery-list-container');
    if (groceryListContainer) {
        groceryListContainer.style.display = 'block';
        groceryListContainer.style.visibility = 'visible';
    }

    console.log('Grocery List Container on DOMContentLoaded:', groceryListContainer);
    console.log('DOM Content:', document.body.innerHTML);
    
    // Fetch recipes and populate dropdowns for the weekly planner
    fetch('/api/recipes')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching recipes:', data.error);
                return;
            }

            const tbody = document.querySelector("#planner tbody");
            tbody.innerHTML = ""; // Clear previous rows

            const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
            days.forEach(day => {
                const row = document.createElement("tr");

                const dayCell = document.createElement("td");
                dayCell.textContent = day;
                row.appendChild(dayCell);

                ["breakfast", "lunch", "dinner"].forEach(meal => {
                    const cell = document.createElement("td");
                    const select = document.createElement("select");
                    select.name = `${day}-${meal}`;
                    select.classList.add("meal-dropdown");

                    // Add default option
                    const defaultOption = document.createElement("option");
                    defaultOption.value = "";
                    defaultOption.textContent = "--Select a Recipe--";
                    select.appendChild(defaultOption);

                    // Populate dropdown options
                    data.forEach(recipe => {
                        const option = document.createElement("option");
                        option.value = recipe.id;
                        option.textContent = recipe.name;
                        select.appendChild(option);
                    });

                    cell.appendChild(select);
                    row.appendChild(cell);
                });

                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching recipes:', error));
});

// Fetch and render the grocery list
async function fetchAndRenderGroceryList(weeklyPlanId) {
    try {
        const response = await fetch('/api/generate_grocery_list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weekly_plan_id: weeklyPlanId }),
        });

        const data = await response.json();
        console.log("API Response:", data); // Debug: Log API response

        if (!data.grocery_list || !Array.isArray(data.grocery_list)) {
            throw new Error('Invalid grocery list format.');
        }

        renderGroceryList(data.grocery_list);
    } catch (error) {
        console.error('Error fetching or rendering grocery list:', error);
    }
}

let remapMode = false; // Track remap mode state

function renderGroceryList(groceryList) {
    const list = document.getElementById('grocery-list');
    list.innerHTML = ''; // Clear previous list

    groceryList.forEach(section => {
        const sectionName = section.section || 'Uncategorized';
        const items = Array.isArray(section.items) ? section.items : [];

        // Create section header
        const sectionHeader = document.createElement('div');
        sectionHeader.className = 'section-header';
        sectionHeader.textContent = sectionName;
        list.appendChild(sectionHeader);

        // Add items to the section
        items.forEach(item => {
            const itemRow = document.createElement('div');
            itemRow.className = 'grocery-item-row';

            // Create checkbox
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'grocery-checkbox';
            checkbox.addEventListener('change', () => toggleStrikeout(itemRow, checkbox));

            // Create main text
            const mainText = document.createElement('span');
            mainText.textContent = item.main_text;
            mainText.className = 'grocery-text';

            // Create precision text
            const precisionText = document.createElement('span');
            precisionText.textContent = ` ${item.precision_text || ''}`;
            precisionText.className = 'precision-text';

            // Append elements
            itemRow.appendChild(checkbox);
            itemRow.appendChild(mainText);
            itemRow.appendChild(precisionText);

            // Add row to the list
            list.appendChild(itemRow);
        });
    });

    togglePrecisionMode(); // Apply precision mode after rendering
}


// Function to enable remapping
function enableRemap(element, item) {
    if (!remapMode) return; // Only allow remapping when in remap mode

    const dropdown = document.createElement('select');
    dropdown.className = 'remap-dropdown';

    const sections = [
        "Pharmacy Section", "Bakery Section", "Deli", "Produce Section",
        "Dairy Section", "Aisle 1: Breakfast Items", "Aisle 2: Baby Products",
        "Aisle 3: Health & Beauty", "Aisle 4: Soup", "Aisle 5: Ethnic Foods",
        "Aisle 6: Candy", "Aisle 7: Condiments & Baking", "Aisle 8: Canned, Dry, Sauces",
        "Aisle 9: Pet Supplies, Magazines, Batteries", "Aisle 10: Cleaning Supplies",
        "Aisle 11: Paper Goods", "Aisle 12: Bread, Water & Snacks",
        "Aisle 13: Frozen Foods Section", "Seafood Section", "Meat Section",
        "Aisle 14: Cheeses, Hotdogs, Frozen Meals", "Aisle 15: Dessert Aisle",
        "Alcohol Section"
    ];

    // Populate dropdown options
    sections.forEach(section => {
        const option = document.createElement('option');
        option.value = section;
        option.textContent = section;
        if (section === item.section) {
            option.selected = true;
        }
        dropdown.appendChild(option);
    });

    // Replace the text element with dropdown
    element.replaceWith(dropdown);

    // Save new section when dropdown loses focus
    dropdown.addEventListener('change', () => {
        item.section = dropdown.value; // Update section in memory
        dropdown.replaceWith(element);
        element.textContent = item.section; // Update UI
    });

    dropdown.focus(); // Automatically focus dropdown
}


// Toggle Remap Mode
function toggleRemapMode() {
    remapMode = !remapMode;
    document.getElementById('remap-mode-button').textContent = remapMode ? "Exit Remap Mode" : "Enter Remap Mode";

    if (remapMode) {
        document.querySelectorAll('.grocery-text').forEach(item => {
            item.addEventListener('click', () => enableRemap(item, { section: item.textContent }));
        });
    }
}


// Save Remaps and Regenerate Grocery List
function saveRemaps() {
    remapMode = false;
    document.getElementById('remap-mode-button').textContent = "Enter Remap Mode";
    fetchAndRenderGroceryList(); // Regenerate list with new mappings
}


// Function to strike out checked items
function toggleStrikeout(item, checkbox) {
    if (checkbox.checked) {
        item.classList.add('strikethrough');
    } else {
        item.classList.remove('strikethrough');
    }
}


document.getElementById('generate-grocery-list').addEventListener('click', () => {
    const plannerData = {
        name: "My Weekly Plan",
        meals: [] // Dynamically populated
    };

    const rows = document.querySelectorAll("#planner tbody tr");
    rows.forEach(row => {
        const day = row.cells[0].textContent; // First cell is the day
        const mealTypes = ["breakfast", "lunch", "dinner"];

        mealTypes.forEach((mealType, index) => {
            const select = row.cells[index + 1].querySelector("select");
            const recipeId = select.value;

            if (recipeId) { // Only add if a recipe is selected
                plannerData.meals.push({
                    day,
                    meal_type: mealType,
                    recipe_id: parseInt(recipeId)
                });
            }
        });
    });

    console.log('Sending plannerData to backend:', plannerData); // Debug

    // Send plannerData to the backend
    fetch('/api/generate_grocery_list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plannerData)
    })
        .then(response => response.json())
        .then(data => {
            console.log('Grocery List API Response:', data); // Debug

            if (data.error) {
                console.error('API Error:', data.error);
                alert('Failed to generate the grocery list.');
                return;
            }

            console.log('Rendering received grocery list:', data.grocery_list); // Debug
            renderGroceryList(data.grocery_list);
        })
        .catch(error => {
            console.error('Error fetching or rendering grocery list:', error);
            alert('An error occurred while generating the grocery list.');
        });
});


// Save the weekly planner
document.getElementById('save-planner').addEventListener('click', () => {
    const plannerData = {
        name: "My Weekly Plan",
        meals: []
    };

    const rows = document.querySelectorAll("#planner tbody tr");

    rows.forEach(row => {
        const day = row.cells[0].textContent;
        const meals = ["breakfast", "lunch", "dinner"];

        meals.forEach((meal, index) => {
            const select = row.cells[index + 1].querySelector("select");
            const recipeId = select.value;

            if (recipeId) {
                plannerData.meals.push({
                    day,
                    meal_type: meal,
                    recipe_id: parseInt(recipeId)
                });
            }
        });
    });

    // Send planner data to the backend
    fetch('/api/weekly_plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plannerData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('Weekly plan saved successfully!');
            } else {
                alert('Failed to save the weekly plan.');
            }
        })
        .catch(error => {
            console.error('Error saving weekly plan:', error);
            alert('An error occurred while saving the weekly plan.');
        });
});

document.getElementById('precision-mode-toggle').addEventListener('change', togglePrecisionMode);
function togglePrecisionMode() {
    const precisionModeEnabled = document.getElementById('precision-mode-toggle').checked;
    const precisionTexts = document.querySelectorAll('.precision-text');

    precisionTexts.forEach(text => {
        if (precisionModeEnabled) {
            text.style.display = "inline"; // Show precision text
        } else {
            text.style.display = "none"; // Hide precision text
        }
    });
}




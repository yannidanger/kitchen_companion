document.addEventListener('DOMContentLoaded', () => {
    const groceryListContainer = document.getElementById('grocery-list-container');
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
    const groceryListContainer = document.getElementById('grocery-list-container');
    try {
        const response = await fetch(`/api/generate_grocery_list`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ weekly_plan_id: weeklyPlanId }),
        });

        if (!response.ok) throw new Error('Failed to fetch grocery list.');

        const data = await response.json();
        console.log('Fetched grocery list:', data);

        if (!data.grocery_list || !Array.isArray(data.grocery_list)) {
            throw new Error('Invalid grocery list structure received.');
        }

        renderGroceryList(data.grocery_list);
    } catch (error) {
        console.error('Error fetching grocery list:', error);
        groceryListContainer.innerHTML = '<p>Error loading grocery list. Please try again later.</p>';
        console.log('Grocery List Container:', document.getElementById('grocery-list-container'));

    }
}

// Render the grocery list
function renderGroceryList(groceryList) {
    const groceryListContainer = document.getElementById('grocery-list-container');
    groceryListContainer.innerHTML = `
        <h2>Your Grocery List</h2>
        <label>
            <input type="checkbox" id="precision-mode-toggle"> Precision Mode
        </label>
        <ul id="grocery-list"></ul>
    `;

    const list = document.getElementById('grocery-list');

    groceryList.forEach((item, index) => {
        console.log(`Processing item at index ${index}:`, item);

        const li = document.createElement('li');
        const mainText = item.main_text || "Unknown Item";
        const precisionText = item.precision_text || "";

        li.innerHTML = `
            <span class="main-text">${mainText}</span>
            <span class="precision-text ${precisionText ? "" : "hidden"}">${precisionText}</span>
        `;
        list.appendChild(li);
    });

    const precisionToggle = document.getElementById('precision-mode-toggle');
    precisionToggle.addEventListener('change', () => {
        const precisionElements = document.querySelectorAll('.precision-text');
        precisionElements.forEach(el => {
            el.classList.toggle('hidden', !precisionToggle.checked);
        });
    });

    precisionToggle.dispatchEvent(new Event('change'));
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

    // Send plannerData to the backend
    console.log('Sending plannerData:', plannerData);

    fetch('/api/generate_grocery_list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plannerData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Grocery List API Response:', data);
        if (data.grocery_list) {
            renderGroceryList(data.grocery_list);
        } else {
            console.error('Invalid response structure:', data);
            alert('Failed to generate the grocery list.');
        }
    })
    .catch(error => {
        console.error('Error generating grocery list:', error);
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

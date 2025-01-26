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

function renderGroceryList(groceryList) {
    const list = document.getElementById('grocery-list');
    list.innerHTML = ''; // Clear previous list

    const isPrecisionMode = document.getElementById('precision-mode-toggle').checked;

    // Save the grocery list in localStorage for dynamic re-rendering
    localStorage.setItem('groceryList', JSON.stringify(groceryList));

    groceryList.forEach(section => {
        const sectionName = section.section || 'Uncategorized';
        const items = Array.isArray(section.items) ? section.items : [];

        // Create section header
        const sectionHeader = document.createElement('li');
        sectionHeader.className = 'section-header';
        sectionHeader.textContent = sectionName;
        list.appendChild(sectionHeader);

        // Render section items
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = isPrecisionMode
                ? `${item.main_text} ${item.precision_text}`
                : item.main_text;
            list.appendChild(li);
        });
    });
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

document.getElementById('precision-mode-toggle').addEventListener('change', () => {
    // Re-render the grocery list when precision mode is toggled
    const groceryList = JSON.parse(localStorage.getItem('groceryList')) || [];
    renderGroceryList(groceryList);
});


document.addEventListener('DOMContentLoaded', () => {
    // Fetch recipes and populate dropdowns
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

document.getElementById('generate-grocery-list').addEventListener('click', () => {
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

    // Send planner data to the backend and redirect
    fetch('/api/generate_grocery_list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plannerData)
    })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.text(); // Rendered HTML from server
        })
        .then(html => {
            document.open();
            document.write(html);
            document.close();
        })
        .catch(error => {
            console.error('Error generating grocery list:', error);
            alert('Failed to generate the grocery list.');
        });
});



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
    console.log("Request URL: /api/weekly_plan");
    fetch('/api/weekly_plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plannerData)
    })

        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
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

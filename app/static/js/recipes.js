function populateFormForEditing(recipe) {
    const add_recipe_form = document.getElementById("add_recipe_form");
    console.log("add_recipe_form:", add_recipe_form); // Debugging
    console.log("add_recipe_form:", document.getElementById("add_recipe_form"));
    console.log("Editing recipe:", recipe);

    if (!add_recipe_form) {
        console.error("add_recipe_form is not found in the DOM!");
        return;
    }
    add_recipe_form.dataset.recipeId = recipe.id;
    document.getElementById("add_recipe_form").dataset.recipeId = recipe.id; // Set the recipe ID
    document.getElementById("recipeName").value = recipe.name || '';
    document.getElementById("cookTime").value = recipe.cook_time || '';
    document.getElementById("servings").value = recipe.servings || '';
    document.getElementById("recipeInstructions").value = recipe.instructions || '';

    const ingredientsContainer = document.getElementById("ingredientsContainer");
    ingredientsContainer.innerHTML = ""; // Clear existing ingredients

    recipe.ingredients.forEach(ingredient => {
        const row = document.createElement("div");
        row.classList.add("ingredient-row");
    
        // Create the unit dropdown dynamically
        const unitDropdown = document.createElement("select");
        unitDropdown.name = "unit";
        unitDropdown.innerHTML = '<option value="">Unit</option>'; // Default option
    
        // Populate unit dropdown with categories and units
        const unitCategories = {
        "Weight/Mass": [
            "Ounce (oz)",
            "Pound (lb)",
            "Gram (g)",
            "Kilogram (kg)",
            "Milligram (mg)",
        ],
        Volume: [
            "Teaspoon (tsp)",
            "Tablespoon (tbsp)",
            "Fluid ounce (fl oz)",
            "Cup",
            "Pint (pt)",
            "Quart (qt)",
            "Gallon (gal)",
            "Milliliter (ml)",
            "Liter (l)",
            "Deciliter (dl)",
        ],
        "Count/Units": [
            "Piece(s) (e.g., 1 apple, 3 eggs)",
            "Dozen (12 units)",
        ],
        "Miscellaneous/Traditional": [
            "Sprig",
            "Block",
            "Dash",
            "Pinch",
            "Drop",
            "Smidgen",
            "Juice of",
            "Zest of",
        ],
        "Specialty Units": [
            "Stick (commonly used for butter in the US)",
            "Can (specific volumes depending on product, e.g., 14 oz for canned tomatoes)",
            "Packet (e.g., yeast, gelatin)",
        ],
        };
    
        Object.entries(unitCategories).forEach(([category, units]) => {
            const categoryOption = document.createElement("option");
            categoryOption.textContent = `-- ${category} --`;
            categoryOption.disabled = true;
            unitDropdown.appendChild(categoryOption);
    
            units.forEach(unit => {
                const option = document.createElement("option");
                option.textContent = unit;
                option.value = unit;
                if (ingredient.unit === unit) {
                    option.selected = true; // Select the correct unit for this ingredient
                }
                unitDropdown.appendChild(option);
            });
        });
    
        // Create ingredient row
        row.innerHTML = `
            <input type="text" value="${ingredient.quantity || ''}" placeholder="Quantity (e.g., 1, 1/2)" name="quantity">
            <select name="size">
                <option value="" ${!ingredient.size ? "selected" : ""}>Size</option>
                <option value="small" ${ingredient.size === "small" ? "selected" : ""}>Small</option>
                <option value="medium" ${ingredient.size === "medium" ? "selected" : ""}>Medium</option>
                <option value="large" ${ingredient.size === "large" ? "selected" : ""}>Large</option>
            </select>
            <input type="text" value="${ingredient.descriptor || ''}" placeholder="Descriptor (e.g., diced, fresh)" name="descriptor">
            <input type="text" value="${ingredient.item_name || ''}" placeholder="Item Name (required)" name="item_name" required>
            <input type="text" value="${ingredient.additional_descriptor || ''}" placeholder="Additional Descriptor" name="additional_descriptor">
            <button type="button" class="removeIngredient" style="background-color: red; color: white;">X</button>
        `;
    
        // Add the dynamically created unit dropdown
        row.querySelector("select[name='size']").before(unitDropdown);
    
        ingredientsContainer.appendChild(row);
    
        // Add remove functionality
        row.querySelector(".removeIngredient").addEventListener("click", () => row.remove());
    });
    

    // Toggle buttons for edit mode
    document.getElementById("saveRecipe").style.display = "none";
    document.getElementById("saveChanges").style.display = "block";
    document.getElementById("cancelEdit").style.display = "block";
}
document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript script started!");

    function resetForm() {
        console.log("Reset form function triggered!");
        const add_recipe_form = document.getElementById("add_recipe_form");
        const ingredientsContainer = document.getElementById("ingredientsContainer");
        const cancelEditButton = document.getElementById("cancelEdit");
        const saveChangesButton = document.getElementById("saveChanges");
        const saveRecipeButton = document.getElementById("saveRecipe");
    
        if (!add_recipe_form || !ingredientsContainer || !cancelEditButton || !saveChangesButton || !saveRecipeButton) {
            console.error("Missing necessary elements for resetForm.");
            return;
        }
    
        console.log("Resetting form...");
        add_recipe_form.reset();
        ingredientsContainer.innerHTML = ""; // Clear ingredient rows
    
        delete add_recipe_form.dataset.recipeId;
    
        saveChangesButton.style.display = "none";
        cancelEditButton.style.display = "none";
        saveRecipeButton.style.display = "block";
    
        console.log("Form reset complete!");
    }

    console.log("All elements found!");

    // Add the cancelEdit button event listener
    const cancelEditButton = document.getElementById("cancelEdit");
    if (cancelEditButton) {
        cancelEditButton.addEventListener("click", resetForm);
        console.log("Cancel Edit button initialized!");
    } else {
        console.error("Cancel Edit button not found in the DOM.");
    }

    // Fetch and populate the recipe dropdown
    async function fetchRecipes() {
        const recipeDropdown = document.getElementById("recipeDropdown");
        try {
            const response = await fetch("/api/recipes");
            if (!response.ok) {
                throw new Error(`Failed to fetch recipes: ${response.statusText}`);
            }
            const recipes = await response.json();
            
            // Script to populate the dropdown with hardcoded units

document.addEventListener("DOMContentLoaded", () => {
    const recipeDropdown = document.getElementById("recipeDropdown");
    recipeDropdown.innerHTML = '<option value="">--Select a Unit--</option>'; // Clear existing options

    // Define unit categories and their options
    const unitCategories = {
        "Weight/Mass": [
            "Ounce (oz)",
            "Pound (lb)",
            "Gram (g)",
            "Kilogram (kg)",
            "Milligram (mg)",
        ],
        Volume: [
            "Teaspoon (tsp)",
            "Tablespoon (tbsp)",
            "Fluid ounce (fl oz)",
            "Cup",
            "Pint (pt)",
            "Quart (qt)",
            "Gallon (gal)",
            "Milliliter (ml)",
            "Liter (l)",
            "Deciliter (dl)",
        ],
        "Count/Units": [
            "Piece(s) (e.g., 1 apple, 3 eggs)",
            "Dozen (12 units)",
        ],
        "Miscellaneous/Traditional": [
            "Sprig",
            "Block",
            "Dash",
            "Pinch",
            "Drop",
            "Smidgen",
            "Juice of",
            "Zest of",
        ],
        "Specialty Units": [
            "Stick (commonly used for butter in the US)",
            "Can (specific volumes depending on product, e.g., 14 oz for canned tomatoes)",
            "Packet (e.g., yeast, gelatin)",
        ],
    };

    // Populate dropdown with categories and units
    Object.entries(unitCategories).forEach(([category, units]) => {
        // Add category as a disabled option
        const categoryOption = document.createElement("option");
        categoryOption.textContent = `-- ${category} --`;
        categoryOption.disabled = true;
        recipeDropdown.appendChild(categoryOption);

        // Add units under the category
        units.forEach(unit => {
            const option = document.createElement("option");
            option.textContent = unit;
            option.value = unit;
            recipeDropdown.appendChild(option);
        });
    });
});

            recipes.forEach(recipe => {
                const option = document.createElement("option");
                option.value = recipe.id;
                option.textContent = recipe.name;
                recipeDropdown.appendChild(option);
            });
        } catch (error) {
            console.error("Error fetching recipes:", error);
            alert("Failed to load recipes. Please try again later.");
        }
    }

    // Handle recipe dropdown change
    const recipeDropdown = document.getElementById("recipeDropdown");
    const recipeContent = document.getElementById("recipeContent");

        // Initially hide the recipe content
        recipeContent.style.display = "none";

        // Listen for dropdown changes
        recipeDropdown.addEventListener("change", async () => {
            const recipeId = recipeDropdown.value;
    
            if (!recipeId) {
                // Hide recipeContent if no recipe is selected
                recipeContent.style.display = "none";
                recipeContent.innerHTML = ""; // Clear content
                resetForm(); // Call your existing resetForm function
                return;
            }
    
            try {
                // Fetch the selected recipe details
const response = await fetch(`/api/recipes/${recipeId}`);
if (!response.ok) {
    throw new Error(`Error fetching recipe: ${response.statusText}`);
}
const recipe = await response.json();

            // Populate the recipeContent
            recipeContent.innerHTML = `
                <h3>${recipe.name}</h3>
                <p><strong>Cook Time:</strong> ${recipe.cook_time || 'N/A'} minutes</p>
                <p><strong>Servings:</strong> ${recipe.servings || 'N/A'}</p>
                <h4>Ingredients:</h4>
                <ul>
                    ${recipe.ingredients && recipe.ingredients.length
                        ? recipe.ingredients.map(ingredient => {
                            if (typeof ingredient === 'object' && ingredient.item_name) {
                                const { quantity = '', unit = '', size = '', descriptor = '', additional_descriptor = '' } = ingredient;
                                return `<li>${quantity} ${unit} ${size} ${descriptor} ${ingredient.item_name}${additional_descriptor ? `, ${additional_descriptor}` : ''}</li>`;
                            } else {
                                console.warn('Unexpected ingredient format:', ingredient);
                                return `<li>Invalid ingredient data</li>`;
                            }
                        }).join('')
                        : '<li>No ingredients listed.</li>'}
                </ul>

                <h4>Instructions:</h4>
                <div style="white-space: pre-wrap; text-indent: 0;">
                    ${recipe.instructions ? recipe.instructions.trim() : 'No instructions available.'}
                </div>

                <div class="button-container">
                    <button id="editRecipe">Edit</button>
                    <button id="deleteRecipe" class="delete-button">Delete</button>
                </div>
            `;

            // Show the recipeContent
            recipeContent.style.display = "block";

            console.log("Rendered recipe content:", recipeContent.innerHTML);

            document.getElementById("editRecipe").addEventListener("click", () => {
                try {
                    populateFormForEditing(recipe);
                } catch (error) {
                    console.error('Error editing recipe:', error);
                }
            });

            document.getElementById("deleteRecipe").addEventListener("click", async () => {
                if (confirm(`Are you sure you want to delete ${recipe.name}?`)) {
                    try {
                        // Add your delete logic here
                    } catch (error) {
                        console.error('Error deleting recipe:', error);
                    }
                }
            });
        } catch (error) {
            console.error("Error fetching recipe:", error);
            alert("Failed to load recipe details.");
        }
    });

    

    // Form submission handler
    const add_recipe_form = document.getElementById("add_recipe_form");
    add_recipe_form.addEventListener("submit", async (e) => {
        e.preventDefault();
        console.log("Form submitted!");

        const recipeId = add_recipe_form.dataset.recipeId; // Check if editing or creating
        const name = document.getElementById("recipeName").value.trim();
        const cookTime = document.getElementById("cookTime").value.trim();
        const servings = document.getElementById("servings").value.trim();
        const instructions = document.getElementById("recipeInstructions").value.trim();

        // Gather ingredients
        const ingredients = Array.from(document.querySelectorAll(".ingredient-row")).map(row => ({
            quantity: row.querySelector('[name="quantity"]').value,
            unit: row.querySelector('[name="unit"]').value,
            size: row.querySelector('[name="size"]').value,
            descriptor: row.querySelector('[name="descriptor"]').value,
            item_name: row.querySelector('[name="item_name"]').value,
            additional_descriptor: row.querySelector('[name="additional_descriptor"]').value,
        }));

        const data = { name, cook_time: cookTime, servings, instructions, ingredients };

        try {
            let response;
            if (recipeId) {
                // Editing an existing recipe (PUT request)
                response = await fetch(`/api/recipes/${recipeId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data),
                });
            } else {
                // Creating a new recipe (POST request)
                response = await fetch("/api/recipes", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data),
                });
            }

            if (!response.ok) {
                throw new Error(`Failed to save recipe: ${response.statusText}`);
            }

            alert(recipeId ? "Recipe updated successfully!" : "Recipe created successfully!");
            location.reload();
        } catch (error) {
            console.error("Error saving recipe:", error);
            alert("Failed to save recipe. Please try again.");
        }
    });

    // Add ingredient row
    // Add ingredient row dynamically with full unit options
document.getElementById("addIngredient").addEventListener("click", () => {
    const ingredientsContainer = document.getElementById("ingredientsContainer");
    const row = document.createElement("div");
    row.classList.add("ingredient-row");

    // Create the unit dropdown with all unit options
    const unitDropdown = document.createElement("select");
    unitDropdown.name = "unit";
    unitDropdown.innerHTML = '<option value="">Unit</option>'; // Default option

    // Populate unit dropdown with categories and units
    const unitCategories = {
        "Weight/Mass": [
            "Ounce (oz)",
            "Pound (lb)",
            "Gram (g)",
            "Kilogram (kg)",
            "Milligram (mg)",
        ],
        Volume: [
            "Teaspoon (tsp)",
            "Tablespoon (tbsp)",
            "Fluid ounce (fl oz)",
            "Cup",
            "Pint (pt)",
            "Quart (qt)",
            "Gallon (gal)",
            "Milliliter (ml)",
            "Liter (l)",
            "Deciliter (dl)",
        ],
        "Count/Units": [
            "Piece(s) (e.g., 1 apple, 3 eggs)",
            "Dozen (12 units)",
        ],
        "Miscellaneous/Traditional": [
            "Sprig",
            "Block",
            "Dash",
            "Pinch",
            "Drop",
            "Smidgen",
            "Juice of",
            "Zest of",
        ],
        "Specialty Units": [
            "Stick (commonly used for butter in the US)",
            "Can (specific volumes depending on product, e.g., 14 oz for canned tomatoes)",
            "Packet (e.g., yeast, gelatin)",
        ],
    };

    Object.entries(unitCategories).forEach(([category, units]) => {
        const categoryOption = document.createElement("option");
        categoryOption.textContent = `-- ${category} --`;
        categoryOption.disabled = true;
        unitDropdown.appendChild(categoryOption);

        units.forEach(unit => {
            const option = document.createElement("option");
            option.textContent = unit;
            option.value = unit;
            unitDropdown.appendChild(option);
        });
    });

    // Create ingredient row with dynamic unit dropdown
    row.innerHTML = `
    <input type="text" placeholder="Quantity (e.g., 1, 1/2)" name="quantity">
    <select name="size">
        <option value="">Size</option>
        <option value="small">Small</option>
        <option value="medium">Medium</option>
        <option value="large">Large</option>
    </select>
    <input type="text" placeholder="Descriptor (e.g., diced, fresh)" name="descriptor">
    <input type="text" placeholder="Item Name (required)" name="item_name" required>
    <input type="text" placeholder="Additional Descriptor" name="additional_descriptor">
    <button type="button" class="removeIngredient">X</button>
`;


    // Add the dynamically created unit dropdown
    row.querySelector("select[name='size']").before(unitDropdown);

    ingredientsContainer.appendChild(row);

    // Add remove functionality
    row.querySelector(".removeIngredient").addEventListener("click", () => row.remove());
});


    // Fetch recipes on page load
    fetchRecipes();
});

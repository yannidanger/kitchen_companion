// Function to populate the form for editing a recipe
function populateFormForEditing(recipe) {
    const add_recipe_form = document.getElementById("add_recipe_form");
    if (!add_recipe_form) {
        console.error("add_recipe_form is not found in the DOM!");
        return;
    }

    add_recipe_form.dataset.recipeId = recipe.id;
    document.getElementById("recipeName").value = recipe.name || '';
    document.getElementById("cookTime").value = recipe.cook_time || '';
    document.getElementById("servings").value = recipe.servings || '';
    document.getElementById("recipeInstructions").value = recipe.instructions || '';

    const ingredientsContainer = document.getElementById("ingredientsContainer");
    ingredientsContainer.innerHTML = ""; // Clear existing ingredients

    recipe.ingredients.forEach(ingredient => {
        const row = document.createElement("div");
        row.classList.add("ingredient-row");

        // Create unit dropdown dynamically
        const unitDropdown = document.createElement("select");
        unitDropdown.name = "unit";
        unitDropdown.innerHTML = '<option value="">Unit</option>'; // Default option

        const unitCategories = {
            "Weight/Mass": ["Ounce (oz)", "Pound (lb)", "Gram (g)", "Kilogram (kg)", "Milligram (mg)"],
            "Volume": ["Teaspoon (tsp)", "Tablespoon (tbsp)", "Cup", "Pint (pt)", "Liter (l)"],
            "Count/Units": ["Piece(s)", "Dozen"],
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
                    option.selected = true;
                }
                unitDropdown.appendChild(option);
            });
        });

        // Add fields to the row
        row.innerHTML = `
            <input type="text" value="${ingredient.quantity || ''}" placeholder="Quantity" name="quantity">
            <select name="size">
                <option value="" ${!ingredient.size ? "selected" : ""}>Size</option>
                <option value="small" ${ingredient.size === "small" ? "selected" : ""}>Small</option>
                <option value="medium" ${ingredient.size === "medium" ? "selected" : ""}>Medium</option>
                <option value="large" ${ingredient.size === "large" ? "selected" : ""}>Large</option>
            </select>
            <input type="text" value="${ingredient.descriptor || ''}" placeholder="Descriptor" name="descriptor">
            <input type="text" value="${ingredient.item_name || ''}" placeholder="Item Name" name="item_name" required>
            <input type="text" value="${ingredient.additional_descriptor || ''}" placeholder="Additional Descriptor" name="additional_descriptor">
            <button type="button" class="removeIngredient" style="background-color: red; color: white;">X</button>
        `;

        row.querySelector("select[name='size']").before(unitDropdown);
        ingredientsContainer.appendChild(row);

        // Remove row functionality
        row.querySelector(".removeIngredient").addEventListener("click", () => row.remove());
    });

    document.getElementById("saveRecipe").style.display = "none";
    document.getElementById("saveChanges").style.display = "block";
    document.getElementById("cancelEdit").style.display = "block";
}

// Function to reset the form
function resetForm() {
    const add_recipe_form = document.getElementById("add_recipe_form");
    const ingredientsContainer = document.getElementById("ingredientsContainer");
    const cancelEditButton = document.getElementById("cancelEdit");
    const saveChangesButton = document.getElementById("saveChanges");
    const saveRecipeButton = document.getElementById("saveRecipe");

    if (!add_recipe_form || !ingredientsContainer || !cancelEditButton || !saveChangesButton || !saveRecipeButton) {
        console.error("Missing elements for resetForm.");
        return;
    }

    add_recipe_form.reset();
    ingredientsContainer.innerHTML = ""; // Clear ingredients
    delete add_recipe_form.dataset.recipeId;

    saveChangesButton.style.display = "none";
    cancelEditButton.style.display = "none";
    saveRecipeButton.style.display = "block";
}

// Fetch recipes from the backend and populate dropdown
async function fetchRecipes() {
    try {
        const response = await fetch("/api/recipes");
        if (!response.ok) {
            throw new Error(`Failed to fetch recipes: ${response.statusText}`);
        }
        const recipes = await response.json();

        const recipeDropdown = document.getElementById("recipeDropdown");
        recipeDropdown.innerHTML = '<option value="">--Select a Recipe--</option>';

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

// Event listener for dropdown change to fetch recipe details
document.getElementById("recipeDropdown").addEventListener("change", async (event) => {
    const recipeId = event.target.value;
    const recipeContent = document.getElementById("recipeContent");
    if (!recipeId) {
        recipeContent.innerHTML = "";
        resetForm();
        return;
    }
    try {
        const response = await fetch(`/api/recipes/${recipeId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch recipe details: ${response.statusText}`);
        }
        const recipe = await response.json();
        populateFormForEditing(recipe);
    } catch (error) {
        console.error("Error fetching recipe details:", error);
        alert("Failed to load recipe details. Please try again.");
    }
});

// Initialize dropdown and events on page load
document.addEventListener("DOMContentLoaded", () => {
    fetchRecipes();

    const cancelEditButton = document.getElementById("cancelEdit");
    if (cancelEditButton) {
        cancelEditButton.addEventListener("click", resetForm);
    }
});

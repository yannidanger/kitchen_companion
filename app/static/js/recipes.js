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
    
        // Check if this ingredient is a sub-recipe
        if (ingredient.ingredient.used_in_recipes && ingredient.ingredient.used_in_recipes.length > 0) {
            row.innerHTML = `
                <span class="sub-recipe" data-recipe-id="${ingredient.ingredient.id}" style="color: green; cursor: pointer;">
                    ${ingredient.ingredient.name} (Sub-Recipe)
                </span>
                <ul class="sub-recipe-ingredients" style="display: none;"></ul>
            `;
    
            // Attach click event to expand/collapse sub-recipe
            row.querySelector(".sub-recipe").addEventListener("click", async (event) => {
                const subRecipeId = event.target.getAttribute("data-recipe-id");
                const subRecipeList = event.target.nextElementSibling;
    
                if (!subRecipeList || !subRecipeId) return;
    
                if (subRecipeList.style.display === "none") {
                    try {
                        const response = await fetch(`/api/recipes/${subRecipeId}`);
                        if (!response.ok) throw new Error(`Error fetching sub-recipe: ${response.statusText}`);
                        const subRecipe = await response.json();
    
                        subRecipeList.innerHTML = subRecipe.ingredients.map(subIngredient => `
                            <li>${subIngredient.quantity} ${subIngredient.unit} - ${subIngredient.ingredient.name}</li>
                        `).join('');
    
                        subRecipeList.style.display = "block";
                    } catch (error) {
                        console.error("❌ Error loading sub-recipe:", error);
                    }
                } else {
                    subRecipeList.style.display = "none";
                }
            });
        } else {
            // Regular ingredient display
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
        }
    
        ingredientsContainer.appendChild(row);
    
        // Add remove functionality for regular ingredients
        if (!row.querySelector(".sub-recipe")) {
            row.querySelector(".removeIngredient").addEventListener("click", () => row.remove());
        }
    });
    
    

    // Toggle buttons for edit mode
    document.getElementById("saveRecipe").style.display = "none";
    document.getElementById("saveChanges").style.display = "block";
    document.getElementById("cancelEdit").style.display = "block";
}
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ JavaScript script started!");

    /** ✅ Initialize Elements **/
    const addIngredientButton = document.getElementById("addIngredient");
    const ingredientsContainer = document.getElementById("ingredientsContainer");
    const subRecipeDropdown = document.getElementById("subRecipeDropdown");
    const addSubRecipeButton = document.getElementById("addSubRecipe");
    const recipeDropdown = document.getElementById("recipeDropdown");
    const add_recipe_form = document.getElementById("add_recipe_form");

    /** ✅ Validate Elements Exist **/
    if (!addIngredientButton) console.error("❌ Add Ingredient button NOT found!");
    if (!ingredientsContainer) console.error("❌ Ingredients container NOT found!");
    if (!subRecipeDropdown) console.error("❌ Sub-Recipe Dropdown NOT found!");
    if (!addSubRecipeButton) console.error("❌ Add Sub-Recipe button NOT found!");
    if (!recipeDropdown) console.error("❌ Recipe Dropdown NOT found!");
    if (!add_recipe_form) console.error("❌ Add Recipe Form NOT found!");

    /** ✅ Add Ingredient Functionality **/
    if (addIngredientButton && ingredientsContainer) {
        addIngredientButton.addEventListener("click", () => {
            console.log("✅ Add Ingredient button clicked!");

            const row = document.createElement("div");
            row.classList.add("ingredient-row");

            // Create unit dropdown
            const unitDropdown = document.createElement("select");
            unitDropdown.name = "unit";
            unitDropdown.innerHTML = '<option value="">Unit</option>'; // Default option

            // Populate unit dropdown
            const unitCategories = {
                "Weight/Mass": ["Ounce (oz)", "Pound (lb)", "Gram (g)", "Kilogram (kg)", "Milligram (mg)"],
                Volume: ["Teaspoon (tsp)", "Tablespoon (tbsp)", "Fluid ounce (fl oz)", "Cup", "Pint (pt)", "Quart (qt)", "Gallon (gal)", "Milliliter (ml)", "Liter (l)", "Deciliter (dl)"],
                "Count/Units": ["Piece(s)", "Dozen"],
                "Miscellaneous/Traditional": ["Sprig", "Block", "Dash", "Pinch", "Drop", "Smidgen", "Juice of", "Zest of"],
                "Specialty Units": ["Stick", "Can", "Packet"],
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

            row.innerHTML = `
                <input type="text" placeholder="Quantity" name="quantity">
                <select name="size">
                    <option value="">Size</option>
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                </select>
                <input type="text" placeholder="Descriptor" name="descriptor">
                <input type="text" placeholder="Item Name (required)" name="item_name" required>
                <input type="text" placeholder="Additional Descriptor" name="additional_descriptor">
                <button type="button" class="removeIngredient">X</button>
            `;

            row.querySelector("select[name='size']").before(unitDropdown);
            ingredientsContainer.appendChild(row);

            row.querySelector(".removeIngredient").addEventListener("click", () => row.remove());
        });

        console.log("✅ Event listener for Add Ingredient attached!");
    }

    /** ✅ Fetch and Populate Recipes **/
    async function fetchRecipes() {
        try {
            const response = await fetch("/api/recipes");
            if (!response.ok) throw new Error(`Failed to fetch recipes: ${response.statusText}`);
            const recipes = await response.json();
    
            recipeDropdown.innerHTML = '<option value="">-- Select a Recipe --</option>';
            
            let regularRecipes = "";
            let subRecipes = "";
    
            recipes.forEach(recipe => {
                const optionHTML = `<option value="${recipe.id}">${recipe.name}</option>`;
    
                // Check if recipe is used in another recipe (meaning it's a sub-recipe)
                if (recipe.used_in_recipes.length > 0) {
                    subRecipes += optionHTML;
                } else {
                    regularRecipes += optionHTML;
                }
            });
    
            recipeDropdown.innerHTML += regularRecipes;
            if (subRecipes) {
                recipeDropdown.innerHTML += `<option disabled>-- Sub-Recipes --</option>` + subRecipes;
            }
    
            console.log("✅ Recipes loaded successfully!");
        } catch (error) {
            console.error("❌ Error fetching recipes:", error);
        }
    }
    
    

    /** ✅ Fetch and Populate Sub-Recipes **/
    async function fetchSubRecipes() {
        try {
            const response = await fetch("/api/recipes");
            if (!response.ok) throw new Error(`Failed to fetch recipes: ${response.statusText}`);
            const recipes = await response.json();

            subRecipeDropdown.innerHTML = '<option value="">--Select a Recipe--</option>';
            recipes.forEach(recipe => {
                const option = document.createElement("option");
                option.value = recipe.id;
                option.textContent = recipe.name;
                subRecipeDropdown.appendChild(option);
            });

            console.log("✅ Sub-Recipes loaded successfully!");
        } catch (error) {
            console.error("❌ Error fetching sub-recipes:", error);
        }
    }

    /** ✅ Add Sub-Recipe Functionality **/
    if (addSubRecipeButton) {
        addSubRecipeButton.addEventListener("click", async () => {
            const parentRecipeId = add_recipe_form.dataset.recipeId;
            const subRecipeId = subRecipeDropdown.value;

            if (!parentRecipeId || !subRecipeId) {
                alert("Please select a recipe and a sub-recipe.");
                return;
            }

            try {
                const response = await fetch(`/api/sub_recipes/${parentRecipeId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ sub_recipe_id: subRecipeId, quantity: 1 })
                });

                if (!response.ok) throw new Error("Failed to add sub-recipe.");

                alert("Sub-recipe added successfully!");
                location.reload();
            } catch (error) {
                console.error("❌ Error adding sub-recipe:", error);
                alert("Could not add sub-recipe.");
            }
        });

        console.log("✅ Event listener for Add Sub-Recipe attached!");
    }

    /** ✅ Fetch Recipes and Sub-Recipes on Load **/
    fetchRecipes();
    fetchSubRecipes();
});

import React, { useEffect, useState } from "react";

function Recipes() {
  const [recipes, setRecipes] = useState([]);
  const [subRecipes, setSubRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [expandedSubRecipes, setExpandedSubRecipes] = useState({});
  const [availableSubRecipes, setAvailableSubRecipes] = useState([]);
  
  const [recipeForm, setRecipeForm] = useState({
    name: "",
    cook_time: "",
    servings: "",
    instructions: "",
    parentRecipeId: "",  // ✅ NEW: Store parent recipe ID
    ingredients: [],  // ✅ NEW: Store ingredients as an array
  });
  
  
  const [editingRecipeId, setEditingRecipeId] = useState(null);
  
  // Add this function to fetch available sub-recipes
const fetchAvailableSubRecipes = async () => {
  try {
    const response = await fetch("http://127.0.0.1:5000/api/sub_recipes/");
    const data = await response.json();
    setAvailableSubRecipes(data);
  } catch (error) {
    console.error("Error fetching available sub-recipes:", error);
  }
};

// Add this function to check for circular references
const checkCircularReference = async (parentId, subRecipeId) => {
  try {
    const response = await fetch("http://127.0.0.1:5000/api/sub_recipes/check_circular", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ parent_id: parentId, sub_recipe_id: subRecipeId })
    });
    const data = await response.json();
    return data.circular;
  } catch (error) {
    console.error("Error checking circular reference:", error);
    return true; // Assume circular to be safe
  }
};

// Add a new function to handle adding a sub-recipe
const addSubRecipe = () => {
  setRecipeForm((prevForm) => ({
    ...prevForm,
    ingredients: [
      ...prevForm.ingredients,
      {
        is_sub_recipe: true,
        sub_recipe_id: "",
        quantity: "1",
        unit: "serving",
      },
    ],
  }));
};

  const fetchRecipes = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/recipes");
      const data = await response.json();
  
      // Remove duplicate recipes (filter by unique recipe ID)
      const uniqueRecipes = data.filter(
        (recipe, index, self) => index === self.findIndex(r => r.id === recipe.id)
      );
  
      setRecipes(uniqueRecipes);
    } catch (error) {
      console.error("Error fetching recipes:", error);
    }
  };
  
  const toggleSubRecipe = async (subRecipeId) => {
    setExpandedSubRecipes(prevState => ({
      ...prevState,
      [subRecipeId]: !prevState[subRecipeId], // Toggle open/closed state
    }));
  
    if (!expandedSubRecipes[subRecipeId]) {
      try {
        const response = await fetch(`http://127.0.0.1:5000/api/sub_recipes/${subRecipeId}`);
        const subRecipe = await response.json();
  
        setSubRecipes((prev) => ({
          ...prev,
          [subRecipeId]: subRecipe.ingredients,
        }));
      } catch (error) {
        console.error("Error loading sub-recipe:", error);
      }
    }
  };

  const fetchSubRecipes = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/sub_recipes");
      const data = await response.json();
  
      if (Array.isArray(data)) {
        setSubRecipes(data);
      } else {
        console.error("Unexpected response format:", data);
      }
    } catch (error) {
      console.error("Error fetching sub-recipes:", error);
    }
  };
  
  
  

  // Handle input changes
  const handleInputChange = (e) => {
    setRecipeForm({ ...recipeForm, [e.target.name]: e.target.value });
  };

  // Add a new ingredient input
  const addIngredient = () => {
    setRecipeForm((prevForm) => ({
      ...prevForm,
      ingredients: [
        ...prevForm.ingredients,
        {
          quantity: "",
          unit: "",
          size: "",
          descriptor: "",
          item_name: "",
          additional_descriptor: "",
        },
      ],
    }));
  };
  
  
  const handleIngredientChange = (index, field, value) => {
    setRecipeForm((prevForm) => {
      const updatedIngredients = prevForm.ingredients.map((ingredient, i) => {
        if (i !== index) return ingredient;
        
        // If changing sub_recipe_id, check for circular reference
        if (field === "sub_recipe_id" && editingRecipeId) {
          checkCircularReference(editingRecipeId, value)
            .then(isCircular => {
              if (isCircular) {
                alert("Can't add this sub-recipe as it would create a circular reference!");
                return { ...ingredient }; // Keep original value
              }
            });
        }
        
        return { ...ingredient, [field]: value };
      });
      return { ...prevForm, ingredients: updatedIngredients };
    });
  };
  
  
  // Remove an ingredient
  const removeIngredient = (index) => {
    const updatedIngredients = recipeForm.ingredients.filter((_, i) => i !== index);
    setRecipeForm({ ...recipeForm, ingredients: updatedIngredients });
  };
  

  // Submit form (Create or Update)
  const handleFormSubmit = async (e) => {
    e.preventDefault();
  
    const method = editingRecipeId ? "PUT" : "POST";
    const url = editingRecipeId
      ? `http://127.0.0.1:5000/api/recipes/${editingRecipeId}`
      : "http://127.0.0.1:5000/api/recipes";
  
    // Prepare ingredients, separating regular ingredients from sub-recipes
    const ingredients = recipeForm.ingredients.map(ingredient => {
      if (ingredient.is_sub_recipe) {
        return {
          sub_recipe_id: ingredient.sub_recipe_id,
          quantity: ingredient.quantity,
          unit: ingredient.unit,
        };
      } else {
        return {
          item_name: ingredient.item_name,
          quantity: ingredient.quantity,
          unit: ingredient.unit,
          size: ingredient.size,
          descriptor: ingredient.descriptor,
          additional_descriptor: ingredient.additional_descriptor
        };
      }
    });
  
    try {
      const response = await fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: recipeForm.name,  
          cook_time: recipeForm.cook_time,
          servings: recipeForm.servings,
          instructions: recipeForm.instructions,
          parent_recipe_id: recipeForm.parentRecipeId || null,
          ingredients: ingredients
        })
      });
  
      if (!response.ok) throw new Error("Failed to save recipe");
  
      alert(editingRecipeId ? "Recipe updated!" : "Recipe added!");
      setRecipeForm({ 
        name: "", 
        cook_time: "", 
        servings: "", 
        instructions: "", 
        ingredients: [] 
      });
      setEditingRecipeId(null);
  
      fetchRecipes();
      fetchSubRecipes();
      fetchAvailableSubRecipes();
  
    } catch (error) {
      console.error("Error saving recipe:", error);
    }
  };
  
  

  const handleDeleteRecipe = async (recipeId) => {
    if (!window.confirm("Are you sure you want to delete this recipe?")) return;
  
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`, {
        method: "DELETE",
      });
  
      if (!response.ok) throw new Error("Failed to delete recipe");
  
      alert("Recipe deleted!");
      fetchRecipes(); // Refresh the dropdown
      fetchSubRecipes()
    } catch (error) {
      console.error("Error deleting recipe:", error);
    }
  };

// Update useEffect to also fetch available sub-recipes
useEffect(() => {
  fetchRecipes();
  fetchSubRecipes();
  fetchAvailableSubRecipes(); // Add this
}, []);
  
  

  // Handle recipe selection
  const handleSelectRecipe = (e) => {
    const recipeId = e.target.value;
    if (recipeId) {
      fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`)
        .then((response) => response.json())
        .then((data) => setSelectedRecipe(data))
        .catch((error) => console.error("Error fetching recipe details:", error));
    } else {
      setSelectedRecipe(null);
    }
  };

  return (
    <div>
      <h1>Recipes</h1>
      <label htmlFor="recipeDropdown">Choose a Recipe:</label>
      <h2>{editingRecipeId ? "Edit Recipe" : "Add a New Recipe"}</h2>
      <form onSubmit={handleFormSubmit} className="recipe-form">
        <div className="form-row">
          <input
            type="text"
            name="name"
            placeholder="Recipe Name"
            value={recipeForm.name}
            onChange={handleInputChange}
            required
          />
          <input
            type="number"
            name="cook_time"
            placeholder="Cook Time (minutes)"
            value={recipeForm.cook_time}
            onChange={handleInputChange}
          />
          <input
            type="number"
            name="servings"
            placeholder="Servings"
            value={recipeForm.servings}
            onChange={handleInputChange}
          />
        </div>

        <h3>Ingredients</h3>
        <div className="ingredient-list">
          {recipeForm.ingredients.map((ingredient, index) => (
            <div key={index} className="ingredient-row">
              {ingredient.is_sub_recipe ? (
                // Sub-recipe inputs
                <>
                  <select
                    value={ingredient.sub_recipe_id || ""}
                    onChange={(e) => handleIngredientChange(index, "sub_recipe_id", e.target.value)}
                    required
                    style={{ flex: "2" }}
                  >
                    <option value="">-- Select Sub-Recipe --</option>
                    {availableSubRecipes.map((subRecipe) => (
                      <option key={subRecipe.id} value={subRecipe.id}>
                        {subRecipe.name}
                      </option>
                    ))}
                  </select>
                  
                  <input
                    type="number"
                    placeholder="Quantity"
                    value={ingredient.quantity || ""}
                    onChange={(e) => handleIngredientChange(index, "quantity", e.target.value)}
                    style={{ flex: "1" }}
                  />
                  
                  <select
                    value={ingredient.unit || "serving"}
                    onChange={(e) => handleIngredientChange(index, "unit", e.target.value)}
                    style={{ flex: "1" }}
                  >
                    <option value="serving">Serving</option>
                    <option value="whole">Whole Recipe</option>
                    <option value="half">Half Recipe</option>
                    <option value="quarter">Quarter Recipe</option>
                  </select>
                  
                  <div className="sub-recipe-tag">Sub-Recipe</div>
                  
                  {/* Remove Sub-Recipe Button */}
                  <button type="button" className="remove-btn" onClick={() => removeIngredient(index)}>X</button>
                </>
              ) : (
                // Regular ingredient inputs
                <>
                  {/* Quantity Input */}
                  <input
                    type="text"
                    placeholder="Quantity"
                    value={ingredient.quantity || ""}
                    onChange={(e) => handleIngredientChange(index, "quantity", e.target.value)}
                  />

                  {/* Unit Dropdown */}
                  <select
                    value={ingredient.unit || ""}
                    onChange={(e) => handleIngredientChange(index, "unit", e.target.value)}
                  >
                    <option value="">Unit</option>
                    <optgroup label="Volume">
                      <option value="tsp">Teaspoon</option>
                      <option value="tbsp">Tablespoon</option>
                      <option value="fl_oz">Fluid Ounce</option>
                      <option value="cup">Cup</option>
                      <option value="pt">Pint</option>
                      <option value="qt">Quart</option>
                      <option value="gal">Gallon</option>
                      <option value="ml">Milliliter</option>
                      <option value="l">Liter</option>
                      <option value="dl">Deciliter</option>
                    </optgroup>
                    <optgroup label="Weight">
                      <option value="oz">Ounce</option>
                      <option value="lb">Pound</option>
                      <option value="g">Gram</option>
                      <option value="kg">Kilogram</option>
                      <option value="mg">Milligram</option>
                    </optgroup>
                    <optgroup label="Count-Based">
                      <option value="piece">Piece</option>
                      <option value="dozen">Dozen</option>
                      <option value="whole">Whole</option>
                    </optgroup>
                    <optgroup label="Specialty">
                      <option value="can">Can</option>
                      <option value="packet">Packet</option>
                      <option value="stick">Stick</option>
                      <option value="block">Block</option>
                    </optgroup>
                  </select>

                  {/* Size Dropdown */}
                  <select
                    value={ingredient.size || ""}
                    onChange={(e) => handleIngredientChange(index, "size", e.target.value)}
                  >
                    <option value="">Size</option>
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                  </select>

                  {/* Descriptor Input */}
                  <input
                    type="text"
                    placeholder="Descriptor (e.g., diced, fresh)"
                    value={ingredient.descriptor || ""}
                    onChange={(e) => handleIngredientChange(index, "descriptor", e.target.value)}
                  />

                  {/* Item Name Input */}
                  <input
                    type="text"
                    placeholder="Item Name (required)"
                    value={ingredient.item_name || ""}
                    onChange={(e) => handleIngredientChange(index, "item_name", e.target.value)}
                    required
                  />

                  {/* Additional Descriptor Input */}
                  <input
                    type="text"
                    placeholder="Additional Descriptor"
                    value={ingredient.additional_descriptor || ""}
                    onChange={(e) => handleIngredientChange(index, "additional_descriptor", e.target.value)}
                  />

                  {/* Remove Ingredient Button */}
                  <button type="button" className="remove-btn" onClick={() => removeIngredient(index)}>X</button>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Add buttons for both regular ingredients and sub-recipes */}
        <div className="add-buttons">
          <button type="button" className="add-btn" onClick={addIngredient}>+ Add Ingredient</button>
          <button type="button" className="add-sub-btn" onClick={addSubRecipe}>+ Add Sub-Recipe</button>
        </div>

        <h3>Instructions</h3>
        <textarea
          name="instructions"
          placeholder="Instructions"
          value={recipeForm.instructions}
          onChange={handleInputChange}
        />

        <h3>Parent Recipe (Optional, for Sub-Recipes)</h3>
        <select
          name="parentRecipeId"
          value={recipeForm.parentRecipeId}
          onChange={handleInputChange}
        >
          <option value="">-- No Parent (Regular Recipe) --</option>
          {recipes.map((recipe) => (
            <option key={recipe.id} value={recipe.id}>
              {recipe.name}
            </option>
          ))}
        </select>

        <button type="submit" className="submit-btn">{editingRecipeId ? "Update Recipe" : "Add Recipe"}</button>
      </form>

      <select id="recipeDropdown" onChange={handleSelectRecipe}>
        <option value="">-- Select a Recipe --</option>

        {/* Regular Recipes */}
        {recipes.length > 0 && (
          <>
            <option disabled>-- Recipes --</option>
            {recipes.map((recipe) => (
              <option key={recipe.id} value={recipe.id}>
                {recipe.name}
              </option>
            ))}
          </>
        )}

        {/* Sub-Recipes Section */}
        {subRecipes.length > 0 && (
          <>
            <option disabled>-- Sub-Recipes --</option>
            {subRecipes.map((subRecipe) => (
              <option key={subRecipe.id} value={subRecipe.id}>
                {subRecipe.name} (Sub)
              </option>
            ))}
          </>
        )}
      </select>

      {/* Single combined recipe display section */}
      {selectedRecipe && (
        <div style={{ marginTop: "20px", border: "1px solid #ccc", padding: "10px" }}>
          <h2>{selectedRecipe.name}</h2>
          <p><strong>Cook Time:</strong> {selectedRecipe.cook_time || "N/A"} minutes</p>
          <p><strong>Servings:</strong> {selectedRecipe.servings || "N/A"}</p>
          
          <h3>Ingredients:</h3>
          <ul>
            {selectedRecipe.ingredients && selectedRecipe.ingredients.length > 0 ? (
              selectedRecipe.ingredients.map((ingredient, index) => {
                // Check if the ingredient is actually a sub-recipe
                if (ingredient.ingredient && 
                    ingredient.ingredient.used_in_recipes && 
                    ingredient.ingredient.used_in_recipes.some(r => r.id)) {
                  return (
                    <li key={index} className="sub-recipe" onClick={() => toggleSubRecipe(ingredient.ingredient.id)}>
                      <span style={{ color: "green", cursor: "pointer" }}>
                        {ingredient.ingredient.name} (Sub-Recipe) ⬇
                      </span>
                      <ul id={`sub-recipe-${ingredient.ingredient.id}`} style={{ display: "none" }}></ul>
                    </li>
                  );
                } else {
                  return (
                    <li key={index}>
                      {ingredient.quantity} {ingredient.unit} - {ingredient.ingredient?.name || "N/A"}
                    </li>
                  );
                }
              })
            ) : (
              <li>No ingredients listed.</li>
            )}
          </ul>
          
          {/* Show sub-recipes if they exist */}
          {selectedRecipe.components && selectedRecipe.components.length > 0 && (
            <>
              <h3>Sub-Recipes:</h3>
              <ul>
                {selectedRecipe.components.map((component, index) => (
                  <li key={`component-${index}`}>
                    {component.quantity} {component.sub_recipe?.name || "Unknown Recipe"}
                    <button 
                      onClick={() => {
                        setSelectedRecipe(component.sub_recipe);
                      }}
                      className="view-sub-btn"
                    >
                      View
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}

          <h3>Instructions:</h3>
          <p>{selectedRecipe.instructions || "No instructions available."}</p>

          {/* Edit Button */}
          <button onClick={() => setEditingRecipeId(selectedRecipe.id)}>
            Edit Recipe
          </button>

          {/* Delete Button */}
          <button onClick={() => handleDeleteRecipe(selectedRecipe.id)} style={{ background: "red", color: "white", marginLeft: "10px" }}>
            Delete Recipe
          </button>
        </div>
      )}
    </div>
  );
}

export default Recipes;
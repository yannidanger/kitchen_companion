import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import IngredientAutocomplete from "../components/IngredientAutocomplete";

function RecipeDetail() {
  const { recipeId } = useParams();
  const navigate = useNavigate();
  const [recipe, setRecipe] = useState(null);
  const [availableSubRecipes, setAvailableSubRecipes] = useState([]);
  const [form, setForm] = useState({
    name: "",
    cook_time: "",
    servings: "",
    instructions: "",
    ingredients: [],
    components: []
  });

  // eslint-disable-next-line no-unused-vars
  const formatFraction = (value) => {
    if (value === null || value === undefined || value === '') return '';

    // Check if the value is a string that might be a fraction
    if (typeof value === 'string' && (value.includes('/') || value.includes(' '))) {
      return value;
    }

    // Check if it's a whole number
    if (Number.isInteger(Number(value))) {
      return String(value);
    }

    // Convert decimal to fraction
    try {
      const decimal = parseFloat(value);
      if (isNaN(decimal)) return String(value)

      // Handle common fractions
      const tolerance = 0.01;
      const commonFractions = [
        { decimal: 0.25, fraction: '1/4' },
        { decimal: 0.33, fraction: '1/3' },
        { decimal: 0.5, fraction: '1/2' },
        { decimal: 0.66, fraction: '2/3' },
        { decimal: 0.75, fraction: '3/4' }
      ];

      for (const frac of commonFractions) {
        if (Math.abs(decimal - frac.decimal) < tolerance) {
          return frac.fraction;
        }
      }

      // For other decimals, convert to fractions
      if (decimal > 0 && decimal < 1) {
        // Try to find a simple fraction (denominator up to 16)
        for (let denominator = 2; denominator <= 16; denominator++) {
          const numerator = Math.round(decimal * denominator);
          if (Math.abs(decimal - numerator / denominator) < tolerance) {
            return `${numerator}/${denominator}`;
          }
        }
      }

      // For mixed numbers (greater than 1)
      if (decimal > 1) {
        const wholePart = Math.floor(decimal);
        const fractionalPart = decimal - wholePart;

        if (fractionalPart > 0) {
          const fractionStr = formatFraction(fractionalPart);
          return fractionStr.includes('/') ? `${wholePart} ${fractionStr}` : value;
        }
      }

      return value;
    } catch (e) {
      return value;
    }
  };


  useEffect(() => {
    // Fetch available sub-recipes
    const fetchAvailableSubRecipes = async () => {
      try {
        const response = await fetch("/api/sub_recipes");
        const data = await response.json();
        setAvailableSubRecipes(data);
      } catch (error) {
        console.error("Error fetching available sub-recipes:", error);
      }
    };

    // Fetch the recipe details
    const fetchRecipe = async () => {
      try {
        const response = await fetch(`/api/recipes/${recipeId}`);
        const data = await response.json();
        console.log("Recipe data from API:", JSON.stringify(data, null, 2));
        setRecipe(data);

        // Process ingredients to use fraction_str if available
        const processedIngredients = data.ingredients.map(ingredient => {
          return {
            ...ingredient,
            // Use fraction_str or the original quantity
            quantity: ingredient.fraction_str || ingredient.quantity
          };
        });

        // Populate the form with the processed ingredients
        setForm({
          name: data.name || "",
          cook_time: data.cook_time || "",
          servings: data.servings || "",
          instructions: data.instructions || "",
          ingredients: processedIngredients,
          components: data.components || []
        });
      } catch (error) {
        console.error("Error fetching recipe:", error);
      }
    };

    fetchAvailableSubRecipes();
    fetchRecipe();
  }, [recipeId]);


  const handleInputChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleIngredientChange = (index, field, value) => {
    setForm((prevForm) => {
      const updatedIngredients = [...prevForm.ingredients];
      updatedIngredients[index] = {
        ...updatedIngredients[index],
        [field]: value
      };
      return { ...prevForm, ingredients: updatedIngredients };
    });
  };

  const handleComponentChange = (index, field, value) => {
    setForm((prevForm) => {
      const updatedComponents = [...prevForm.components];
      updatedComponents[index] = {
        ...updatedComponents[index],
        [field]: value
      };
      return { ...prevForm, components: updatedComponents };
    });
  };

  const addIngredient = () => {
    setForm((prevForm) => ({
      ...prevForm,
      ingredients: [
        ...prevForm.ingredients,
        {
          quantity: "",
          unit: "",
          item_name: "",
          size: "",
          descriptor: "",
          additional_descriptor: ""
        },
      ],
    }));
  };

  const addSubRecipe = () => {
    setForm((prevForm) => ({
      ...prevForm,
      components: [
        ...prevForm.components,
        {
          quantity: 1,
          sub_recipe: { id: "", name: "" }
        },
      ],
    }));
  };

  const removeIngredient = (index) => {
    setForm((prevForm) => ({
      ...prevForm,
      ingredients: prevForm.ingredients.filter((_, i) => i !== index)
    }));
  };

  const removeComponent = (index) => {
    setForm((prevForm) => ({
      ...prevForm,
      components: prevForm.components.filter((_, i) => i !== index)
    }));
  };

  // Handle select from USDA autocomplete
  const handleIngredientSelect = (index, selectedIngredient) => {
    setForm((prevForm) => {
      const updatedIngredients = [...prevForm.ingredients];
      updatedIngredients[index] = {
        ...updatedIngredients[index],
        item_name: selectedIngredient.name,
        display_name: selectedIngredient.display_name || selectedIngredient.name,
        ingredient_id: selectedIngredient.id,
        usda_fdc_id: selectedIngredient.isUsda ? selectedIngredient.id : null,
        is_custom: !selectedIngredient.isUsda
      };
      return { ...prevForm, ingredients: updatedIngredients };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      console.log("Form data before submission:", form);

      // Prepare the payload with separate handling for ingredients and sub-recipes
      const payload = {
        name: form.name,
        cook_time: form.cook_time,
        servings: form.servings,
        instructions: form.instructions,
        ingredients: []
      };

      // Add regular ingredients
      form.ingredients.forEach(ingredient => {
        // Only add if it has a name
        if (ingredient.item_name || (ingredient.ingredient && ingredient.ingredient.name)) {
          const ingredientPayload = {
            id: ingredient.id,
            item_name: ingredient.item_name || (ingredient.ingredient ? ingredient.ingredient.name : ""),
            quantity: ingredient.quantity,
            unit: ingredient.unit,
            size: ingredient.size || "",
            descriptor: ingredient.descriptor || "",
            additional_descriptor: ingredient.additional_descriptor || ""
          };
          
          // Add USDA data if available
          if (ingredient.usda_fdc_id) {
            ingredientPayload.usda_fdc_id = ingredient.usda_fdc_id;
          }
          if (ingredient.ingredient_id) {
            ingredientPayload.ingredient_id = ingredient.ingredient_id;
          }
          
          payload.ingredients.push(ingredientPayload);
        }
      });

      // Add sub-recipes
      if (form.components && form.components.length > 0) {
        form.components.forEach(component => {
          // Only add if it has a valid sub-recipe reference
          if (component.sub_recipe && component.sub_recipe.id) {
            payload.ingredients.push({
              sub_recipe_id: component.sub_recipe.id,
              quantity: component.quantity || 1,
              unit: "serving" // Default unit for sub-recipes
            });
          }
        });
      }

      console.log("Payload being sent to API:", JSON.stringify(payload, null, 2));

      const response = await fetch(`/api/recipes/${recipeId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to update recipe: ${errorData.error || "Unknown error"}`);
      }

      alert("Recipe updated!");
      navigate("/recipe-management");
    } catch (error) {
      console.error("Error updating recipe:", error);
      alert("Error updating recipe: " + error.message);
    }
  };

  return (
    <div className="recipe-detail-container">
      <div className="recipe-detail-header">
        <h2>Edit Recipe</h2>
      </div>

      {recipe ? (
        <form className="recipe-detail-form" onSubmit={handleSubmit}>
          {/* Basic Recipe Information */}
          <div className="form-group">
            <label htmlFor="recipe-name">Recipe Name</label>
            <input
              id="recipe-name"
              type="text"
              name="name"
              value={form.name}
              onChange={handleInputChange}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cook-time">Cook Time (minutes)</label>
              <input
                id="cook-time"
                type="text"
                name="cook_time"
                value={form.cook_time}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="servings">Servings</label>
              <input
                id="servings"
                type="number"
                name="servings"
                value={form.servings}
                onChange={handleInputChange}
              />
            </div>
          </div>

          {/* Ingredients Section */}
          <h3 className="section-header">Ingredients</h3>
          <p className="helper-text">Format: Quantity | Unit | Size | Descriptor | Ingredient Name | Additional Descriptor</p>

          <div className="ingredients-section">
            {form.ingredients && form.ingredients.length > 0 ? (
              form.ingredients.map((ingredient, index) => {
                // Skip ingredient if it's actually a sub-recipe component
                if (ingredient.sub_recipe_id) return null;

                return (
                  <div key={index} className="ingredient-row">
                    <input
                      className="qty-field"
                      type="text"
                      placeholder="Quantity (e.g., 1/2, 1 1/2)"
                      value={ingredient.quantity || ""}
                      onChange={(e) => handleIngredientChange(index, "quantity", e.target.value)}
                    />
                    <select
                      className="unit-field"
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
                        <option value="sprig">Sprig</option>
                      </optgroup>
                    </select>
                    <select
                      className="size-field"
                      value={ingredient.size || ""}
                      onChange={(e) => handleIngredientChange(index, "size", e.target.value)}
                    >
                      <option value="">Size</option>
                      <option value="small">Small</option>
                      <option value="medium">Medium</option>
                      <option value="large">Large</option>
                    </select>
                    <input
                      className="descriptor-field"
                      type="text"
                      placeholder="Descriptor (e.g., fresh)"
                      value={ingredient.descriptor || ""}
                      onChange={(e) => handleIngredientChange(index, "descriptor", e.target.value)}
                    />
                    
                    {/* Replace standard input with IngredientAutocomplete */}
                    <IngredientAutocomplete
                      value={ingredient.item_name || (ingredient.ingredient ? ingredient.ingredient.name : "")}
                      onChange={(value) => handleIngredientChange(index, "item_name", value)}
                      onSelect={(selectedIngredient) => handleIngredientSelect(index, selectedIngredient)}
                      placeholder="Ingredient Name"
                      required
                    />
                    
                    <input
                      className="descriptor-field"
                      type="text"
                      placeholder="Additional (e.g., chopped)"
                      value={ingredient.additional_descriptor || ""}
                      onChange={(e) => handleIngredientChange(index, "additional_descriptor", e.target.value)}
                    />
                    <button
                      type="button"
                      className="remove-button"
                      onClick={() => removeIngredient(index)}
                    >
                      ✕
                    </button>
                  </div>
                );
              })
            ) : (
              <p>No ingredients yet. Add some below.</p>
            )}

            <button type="button" className="add-button" onClick={addIngredient}>
              <span className="add-button-icon">+</span> Add Ingredient
            </button>
          </div>

          {/* Sub-Recipes Section */}
          <h3 className="section-header">Sub-Recipes</h3>

          <div className="sub-recipes-section">
            {form.components && form.components.length > 0 ? (
              form.components.map((component, index) => (
                <div key={index} className="sub-recipe-row">
                  <select
                    className="sub-recipe-select"
                    value={component.sub_recipe?.id || ""}
                    onChange={(e) => {
                      const selectedId = e.target.value;
                      const selectedRecipe = availableSubRecipes.find(r => r.id.toString() === selectedId);
                      handleComponentChange(index, "sub_recipe", {
                        id: selectedId,
                        name: selectedRecipe ? selectedRecipe.name : ""
                      });
                    }}
                    required
                  >
                    <option value="">-- Select Sub-Recipe --</option>
                    {availableSubRecipes.map((subRecipe) => (
                      <option key={subRecipe.id} value={subRecipe.id}>
                        {subRecipe.name}
                      </option>
                    ))}
                  </select>
                  <input
                    className="qty-field"
                    type="number"
                    placeholder="Quantity"
                    value={component.quantity || ""}
                    onChange={(e) => handleComponentChange(index, "quantity", e.target.value)}
                    min="0.1"
                    step="0.1"
                  />
                  <span className="sub-recipe-unit">servings</span>
                  <button
                    type="button"
                    className="remove-button"
                    onClick={() => removeComponent(index)}
                  >
                    ✕
                  </button>
                </div>
              ))
            ) : (
              <p>No sub-recipes yet. Add some below.</p>
            )}

            <button type="button" className="add-button add-sub-button" onClick={addSubRecipe}>
              <span className="add-button-icon">+</span> Add Sub-Recipe
            </button>
          </div>

          {/* Instructions Section */}
          <div className="form-group">
            <label htmlFor="instructions">Instructions</label>
            <textarea
              id="instructions"
              name="instructions"
              value={form.instructions}
              onChange={handleInputChange}
              placeholder="Enter detailed cooking instructions..."
            />
          </div>

          {/* Form Actions */}
          <div className="form-actions">
            <button type="button" className="cancel-button" onClick={() => navigate("/recipe-management")}>
              Cancel
            </button>
            <button type="submit" className="save-button">
              Save Changes
            </button>
          </div>
        </form>
      ) : (
        <div className="loading-container">
          <p>Loading recipe...</p>
        </div>
      )}
    </div>
  );
}

export default RecipeDetail;
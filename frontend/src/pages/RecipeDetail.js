import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./RecipeDetail.css"; // Make sure to import the enhanced CSS

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
  

  useEffect(() => {
    // Fetch available sub-recipes
    const fetchAvailableSubRecipes = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/api/sub_recipes/");
        const data = await response.json();
        setAvailableSubRecipes(data);
      } catch (error) {
        console.error("Error fetching available sub-recipes:", error);
      }
    };

    // Fetch the recipe details
    const fetchRecipe = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`);
        const data = await response.json();
        console.log("Recipe data from API:", JSON.stringify(data, null, 2));
        setRecipe(data);
        
        // Populate the form
        setForm({
          name: data.name || "",
          cook_time: data.cook_time || "",
          servings: data.servings || "",
          instructions: data.instructions || "",
          ingredients: data.ingredients || [], 
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
          payload.ingredients.push({
            id: ingredient.id,
            item_name: ingredient.item_name || (ingredient.ingredient ? ingredient.ingredient.name : ""),
            quantity: ingredient.quantity,
            unit: ingredient.unit,
            size: ingredient.size || "",
            descriptor: ingredient.descriptor || "",
            additional_descriptor: ingredient.additional_descriptor || ""
          });
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
      
      const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`, {
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
                type="number" 
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
                      type="number"
                      placeholder="Quantity"
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
                    <input
                      className="name-field"
                      type="text"
                      placeholder="Ingredient Name"
                      value={ingredient.item_name || (ingredient.ingredient ? ingredient.ingredient.name : "")}
                      onChange={(e) => handleIngredientChange(index, "item_name", e.target.value)}
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
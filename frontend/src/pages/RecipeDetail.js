import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

function RecipeDetail() {
  const { recipeId } = useParams();
  const navigate = useNavigate();
  const [recipe, setRecipe] = useState(null);
  const [form, setForm] = useState({
    name: "",
    cook_time: "",
    servings: "",
    instructions: "",
    ingredients: [], // ✅ Add ingredients to state
  });
  

  useEffect(() => {
    const fetchRecipe = async () => {
        try {
          const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`);
          const data = await response.json();
          setRecipe(data);
          setForm({
            name: data.name,
            cook_time: data.cook_time || "",
            servings: data.servings || "",
            instructions: data.instructions || "",
            ingredients: data.ingredients || [], // ✅ Ensure ingredients are loaded
          });
        } catch (error) {
          console.error("Error fetching recipe:", error);
        }
      };
      
  
    fetchRecipe();
  }, [recipeId]);
  

  const handleInputChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleIngredientChange = (index, field, value) => {
    setForm((prevForm) => {
      const updatedIngredients = prevForm.ingredients.map((ingredient, i) =>
        i === index ? { ...ingredient, [field]: value } : ingredient
      );
      return { ...prevForm, ingredients: updatedIngredients };
    });
  };
  

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`, {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json" // ✅ Ensure this is set
        },
        body: JSON.stringify({
          ...form,
          ingredients: form.ingredients.map(ingredient => ({
            id: ingredient.id,
            item_name: ingredient.item_name || "",
            quantity: ingredient.quantity,
            unit: ingredient.unit,
            size: ingredient.size || "",
            descriptor: ingredient.descriptor || "",
            additional_descriptor: ingredient.additional_descriptor || ""
          }))
        }),
      });
  
      if (!response.ok) throw new Error("Failed to update recipe");
  
      alert("Recipe updated!");
      navigate("/recipe-management");
    } catch (error) {
      console.error("Error updating recipe:", error);
    }
  };
  
  

  return (
    <div>
      <h2>Edit Recipe</h2>
      {recipe ? (
        <form onSubmit={handleSubmit}>
  <label>
    Recipe Name:
    <input type="text" name="name" value={form.name} onChange={handleInputChange} required />
  </label>

  <label>
    Cook Time (minutes):
    <input type="number" name="cook_time" value={form.cook_time} onChange={handleInputChange} />
  </label>

  <label>
    Servings:
    <input type="number" name="servings" value={form.servings} onChange={handleInputChange} />
  </label>

  <label>
    Instructions:
    <textarea name="instructions" value={form.instructions} onChange={handleInputChange} />
  </label>

  <h3>Ingredients</h3>
{form.ingredients.length > 0 ? (
  form.ingredients.map((ingredient, index) => (
    <div key={index} className="ingredient-row">
      {/* Item Name */}
      <input
        type="text"
        placeholder="Ingredient Name"
        value={ingredient.item_name || ""}
        onChange={(e) => handleIngredientChange(index, "item_name", e.target.value)}
        required
      />

      {/* Quantity */}
      <input
        type="number"
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

      {/* Descriptor 1 */}
      <input
        type="text"
        placeholder="Descriptor (e.g., diced, fresh)"
        value={ingredient.descriptor || ""}
        onChange={(e) => handleIngredientChange(index, "descriptor", e.target.value)}
      />

      {/* Additional Descriptor */}
      <input
        type="text"
        placeholder="Additional Descriptor"
        value={ingredient.additional_descriptor || ""}
        onChange={(e) => handleIngredientChange(index, "additional_descriptor", e.target.value)}
      />
    </div>
  ))
) : (
  <p>No ingredients found</p>
)}


  <button type="submit">Save Changes</button>
</form>

      
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

export default RecipeDetail;

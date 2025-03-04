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

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
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
          <input type="text" name="name" value={form.name} onChange={handleInputChange} required />
          <input type="number" name="cook_time" value={form.cook_time} onChange={handleInputChange} placeholder="Cook Time" />
          <input type="number" name="servings" value={form.servings} onChange={handleInputChange} placeholder="Servings" />
          <textarea name="instructions" value={form.instructions} onChange={handleInputChange} placeholder="Instructions" />
          <button type="submit">Save Changes</button>
        </form>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

export default RecipeDetail;

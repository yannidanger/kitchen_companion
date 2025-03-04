import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";


function RecipeManagement() {
  const [recipes, setRecipes] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRecipes();
  }, []);

  const fetchRecipes = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/recipes");
      const data = await response.json();
      setRecipes(data);
    } catch (error) {
      console.error("Error fetching recipes:", error);
    }
  };

  const handleDelete = async (recipeId) => {
    if (!window.confirm("Are you sure you want to delete this recipe?")) return;

    try {
      const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete recipe");

      alert("Recipe deleted!");
      fetchRecipes(); // Refresh list after deletion
    } catch (error) {
      console.error("Error deleting recipe:", error);
    }
  };

  return (
    <div>
      <h2>Manage Recipes</h2>
      <p>Click a recipe to view or edit, or delete it.</p>

      <ul className="recipe-list">
        {recipes.map((recipe) => (
          <li key={recipe.id} className="recipe-item">
            <span className="recipe-name">{recipe.name}</span>
            <button onClick={() => navigate(`/recipes/${recipe.id}/edit`)}>✏ Edit</button>
            <button className="delete-btn" onClick={() => handleDelete(recipe.id)}>🗑 Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default RecipeManagement;

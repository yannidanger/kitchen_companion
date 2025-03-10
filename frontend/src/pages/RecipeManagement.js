import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import RecipeTreeView from "../components/RecipeTreeView"; // Updated import path

function RecipeManagement() {
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortOrder, setSortOrder] = useState("name-asc");
  const navigate = useNavigate();

  useEffect(() => {
    fetchRecipes();
  }, []);

  // Fetch all recipes
  const fetchRecipes = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/recipes");
      const data = await response.json();
      setRecipes(data);
    } catch (error) {
      console.error("Error fetching recipes:", error);
    }
  };

  // Fetch a single recipe with details
  const fetchRecipeDetails = async (recipeId) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`);
      const data = await response.json();
      console.log("Recipe data from API:", JSON.stringify(data, null, 2));
      setSelectedRecipe(data);
    } catch (error) {
      console.error("Error fetching recipe details:", error);
    }
  };
  // Delete recipe
  const handleDelete = async (recipeId) => {
    if (!window.confirm("Are you sure you want to delete this recipe?")) return;

    try {
      const response = await fetch(`http://127.0.0.1:5000/api/recipes/${recipeId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete recipe");

      // Clear selected recipe if it's the one we deleted
      if (selectedRecipe && selectedRecipe.id === recipeId) {
        setSelectedRecipe(null);
      }

      fetchRecipes(); // Refresh list after deletion
    } catch (error) {
      console.error("Error deleting recipe:", error);
    }
  };

  // Toggle fullscreen mode
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Handle search input change
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  // Handle sort order change
  const handleSortChange = (e) => {
    setSortOrder(e.target.value);
  };

  // Sort and filter recipes
  const filteredAndSortedRecipes = React.useMemo(() => {
    // First filter
    const filtered = recipes.filter(recipe => 
      recipe.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Then sort
    return filtered.sort((a, b) => {
      switch(sortOrder) {
        case "name-asc":
          return a.name.localeCompare(b.name);
        case "name-desc":
          return b.name.localeCompare(a.name);
        // Add more sort options as needed
        default:
          return 0;
      }
    });
  }, [recipes, searchTerm, sortOrder]);


  return (
    <div className={`recipe-management ${isFullscreen ? 'fullscreen' : ''}`}>
      <div className="recipe-management-header">
        <h2>Recipe Management</h2>
        <div className="recipe-controls">
          <div className="search-container">
            <input
              type="text"
              placeholder="Search recipes..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="search-input"
            />
          </div>
          <div className="sort-container">
            <select 
              value={sortOrder}
              onChange={handleSortChange}
              className="sort-select"
            >
              <option value="name-asc">Name (A-Z)</option>
              <option value="name-desc">Name (Z-A)</option>
              {/* Add more sort options as needed */}
            </select>
          </div>
        </div>
      </div>

      <div className="recipe-management-content">
        {/* Recipe List (left panel) */}
        <div className={`recipe-list-panel ${selectedRecipe && isFullscreen ? 'hidden' : ''}`}>
          <h3>Recipes</h3>
          {filteredAndSortedRecipes.length > 0 ? (
            <ul className="recipe-list">
              {filteredAndSortedRecipes.map((recipe) => (
                <li 
                  key={recipe.id} 
                  className={`recipe-item ${selectedRecipe?.id === recipe.id ? 'selected' : ''}`}
                  onClick={() => fetchRecipeDetails(recipe.id)}
                >
                  <span className="recipe-name">{recipe.name}</span>
                  <div className="recipe-actions">
                    <button 
                      className="edit-btn" 
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/recipes/${recipe.id}/edit`);
                      }}
                    >
                      ✏️
                    </button>
                    <button 
                      className="delete-btn" 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(recipe.id);
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>No recipes found. Try adjusting your search or add a new recipe.</p>
          )}
        </div>

        {/* Recipe Details (right panel) */}
        <div className={`recipe-detail-panel ${selectedRecipe ? '' : 'empty'} ${isFullscreen ? 'fullscreen' : ''}`}>
          {selectedRecipe ? (
            <div className="recipe-detail">
              <div className="recipe-detail-header">
                <h3>{selectedRecipe.name}</h3>
                <div className="recipe-detail-actions">
                  <button 
                    className="fullscreen-btn" 
                    onClick={toggleFullscreen}
                  >
                    {isFullscreen ? '⊞' : '⛶'}
                  </button>
                  <button 
                    className="edit-btn" 
                    onClick={() => navigate(`/recipes/${selectedRecipe.id}/edit`)}
                  >
                    Edit
                  </button>
                  <button 
                    className="delete-btn" 
                    onClick={() => handleDelete(selectedRecipe.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              <div className="recipe-detail-info">
                <p><strong>Cook Time:</strong> {selectedRecipe.cook_time || "N/A"} minutes</p>
                <p><strong>Servings:</strong> {selectedRecipe.servings || "N/A"}</p>
              </div>
              
              <div className="recipe-detail-ingredients">
                <h4>Ingredients:</h4>
                {selectedRecipe.ingredients && selectedRecipe.ingredients.length > 0 ? (
                  <ul className="ingredients-list">
                    {selectedRecipe.ingredients.map((ingredient, index) => (
                      <li key={index}>
                        {ingredient.fraction_str || ingredient.quantity} {ingredient.unit}
                        {ingredient.size ? ` ${ingredient.size}` : ''} 
                        {ingredient.descriptor ? ` ${ingredient.descriptor} ` : ' '}
                        {ingredient.ingredient?.name || "N/A"}
                        {ingredient.additional_descriptor ? `, ${ingredient.additional_descriptor}` : ''}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No ingredients listed.</p>
                )}
              </div>
              
              {/* Sub-recipes section */}
              {selectedRecipe.components && selectedRecipe.components.length > 0 && (
                <div className="recipe-detail-sub-recipes">
                  <h4>Sub-recipes:</h4>
                  <div className="sub-recipes-tree">
                    <RecipeTreeView recipe={selectedRecipe} initialExpanded={true} />
                  </div>
                </div>
              )}
              
              <div className="recipe-detail-instructions">
                <h4>Instructions:</h4>
                <p>{selectedRecipe.instructions || "No instructions available."}</p>
              </div>
            </div>
          ) : (
            <div className="no-recipe-selected">
              <p>Select a recipe from the list to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default RecipeManagement;
import React, { useState } from 'react';

function RecipeTreeView({ recipe, initialExpanded = false }) {
  // Local state for expanded/collapsed state of this recipe
  const [expanded, setExpanded] = useState(initialExpanded);

  // If no recipe, render nothing
  if (!recipe) return null;

  // Determine if this recipe has sub-recipes
  const hasSubRecipes = recipe.components && recipe.components.length > 0;

  // Click handler for toggling expansion
  const toggleExpand = (e) => {
    // Prevent event bubbling to parent recipe nodes
    e.stopPropagation();
    setExpanded(!expanded);
  };

  return (
    <div className="recipe-tree-node">
      {/* Recipe header - always visible */}
      <div 
        className={`recipe-tree-header ${hasSubRecipes ? 'has-children' : ''}`}
        onClick={toggleExpand}
        style={hasSubRecipes ? { cursor: 'pointer' } : {}}
      >
        {hasSubRecipes && (
          <span className="recipe-tree-toggle">
            {expanded ? '▼' : '►'}
          </span>
        )}
        <span className="recipe-tree-name">{recipe.name}</span>
      </div>

      {/* Expanded content - only visible when expanded is true */}
      {expanded && (
        <div className="recipe-tree-content">
          {/* Ingredients */}
          {recipe.ingredients && recipe.ingredients.length > 0 && (
            <div className="recipe-tree-ingredients">
              <h5>Ingredients:</h5>
              <ul>
              {recipe.ingredients.map((ingredient, idx) => (
                <li key={idx}>
                    {ingredient.quantity} {ingredient.unit}
                    {ingredient.size ? ` ${ingredient.size}` : ''} 
                    {ingredient.descriptor ? ` ${ingredient.descriptor} ` : ' '}
                    {ingredient.ingredient?.name || "N/A"}
                    {ingredient.additional_descriptor ? `, ${ingredient.additional_descriptor}` : ''}
                </li>
                ))}
              </ul>
            </div>
          )}

          {/* Instructions if available */}
          {recipe.instructions && (
            <div className="recipe-tree-instructions">
              <h5>Instructions:</h5>
              <p>{recipe.instructions}</p>
            </div>
          )}

          {/* Sub-recipes */}
          {hasSubRecipes && (
            <div className="recipe-tree-sub-recipes">
              <h5>Sub-recipes:</h5>
              {recipe.components.map((component, idx) => {
                // Get the sub-recipe
                const subRecipe = component.sub_recipe;
                
                if (!subRecipe) return null;
                
                // Check for circular reference
                const isCircular = subRecipe.id === recipe.id;
                
                if (isCircular) {
                  return (
                    <div key={idx} className="recipe-tree-sub-recipe">
                      <div className="recipe-tree-sub-recipe-header recursive-warning">
                        <span className="recipe-tree-warning">⚠️</span>
                        <span>{subRecipe.name} (recursive reference)</span>
                      </div>
                    </div>
                  );
                }
                
                return (
                  <div key={idx} className="recipe-tree-sub-recipe">
                    <div className="recipe-tree-sub-recipe-header">
                      <span className="recipe-tree-quantity">
                        {component.quantity} 
                      </span>
                      {/* Create a NEW instance of RecipeTreeView for each sub-recipe */}
                      <RecipeTreeView 
                        recipe={subRecipe}
                        initialExpanded={false}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default RecipeTreeView;
// src/components/GroceryListItem.js
import React, { useState } from 'react';
import '../styles/GroceryListStyles.css';

/**
 * GroceryListItem component displays an individual ingredient in the grocery list
 * with visual indicators for USDA vs custom ingredients
 */
const GroceryListItem = ({ item, onToggleComplete }) => {
  const [completed, setCompleted] = useState(false);
  
  // Handle checkbox toggle
  const handleToggle = () => {
    const newState = !completed;
    setCompleted(newState);
    if (onToggleComplete) {
      onToggleComplete(item, newState);
    }
  };
  
  // Extract source recipes
  const sources = item.quantities && Array.isArray(item.quantities)
    ? [...new Set(item.quantities
        .filter(q => q.source)
        .map(q => q.source))]
    : [];
  
  return (
    <div className={`grocery-item ${completed ? 'completed' : ''}`}>
      <input 
        type="checkbox" 
        className="item-checkbox" 
        checked={completed}
        onChange={handleToggle}
      />
      
      <div className="item-info">
        <div className="item-name">
          {item.name}
          
          {/* USDA or Custom badge */}
          {item.is_usda ? (
            <span className="ingredient-badge usda-badge">USDA</span>
          ) : (
            <span className="ingredient-badge custom-badge">Custom</span>
          )}
        </div>
        
        <div className="item-quantity">
          {/* Show combined quantity if available, otherwise show the first quantity */}
          {item.formatted_combined || (item.quantities && item.quantities.length > 0 ? item.quantities[0].quantity_text : '')}
          
          {/* If there are multiple units, show this information */}
          {item.has_multiple_units && (
            <span className="multiple-units"> (multiple units)</span>
          )}
        </div>
        
        {/* Show source recipes if available */}
        {sources.length > 0 && (
          <div className="item-recipes">
            From: {sources.join(', ')}
          </div>
        )}
      </div>
    </div>
  );
};

export default GroceryListItem;
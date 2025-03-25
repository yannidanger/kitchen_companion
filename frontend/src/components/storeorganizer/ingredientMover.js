import React from "react";

const IngredientMover = ({ 
    sections, 
    targetSection, 
    setTargetSection, 
    moveSelectedIngredients, 
    clearSelections,
    selectedIngredients = {},
    filteredCount = 0,
    totalCount = "all"
}) => {
    // Count selected ingredients
    const selectedCount = Object.values(selectedIngredients).filter(Boolean).length;

    return (
        <div className="ingredient-mover">
            <div className="mover-heading">
                <h3>Move Ingredients Between Sections</h3>
                <div className="selection-counter">
                    <span>{selectedCount} selected</span>
                    <div className="total-counter">
                        {totalCount === "filtered" 
                            ? `Showing ${filteredCount} filtered ingredients` 
                            : `${filteredCount} ingredients total`}
                    </div>
                </div>
            </div>
            
            <div className="mover-controls">
                <div className="target-section-selector">
                    <label htmlFor="target-section">Move selected ingredients to:</label>
                    <select
                        id="target-section"
                        value={targetSection}
                        onChange={(e) => setTargetSection(e.target.value)}
                    >
                        <option value="">Select a section</option>
                        {sections.map(section => (
                            <option key={section.id} value={section.id}>
                                {section.name}
                            </option>
                        ))}
                    </select>
                </div>
                
                <div className="mover-buttons">
                    <button 
                        className="move-btn"
                        onClick={moveSelectedIngredients}
                        disabled={!targetSection || selectedCount === 0}
                    >
                        Move Selected
                    </button>
                    
                    <button 
                        className="clear-btn"
                        onClick={clearSelections}
                        disabled={selectedCount === 0}
                    >
                        Clear Selection
                    </button>
                </div>
            </div>

            <div className="mover-instructions">
                <p>1. Check the ingredients you want to organize</p>
                <p>2. Select a destination section from the dropdown</p>
                <p>3. Click "Move Selected" to reorganize your ingredients</p>
            </div>
        </div>
    );
};

export default IngredientMover;
import React from "react";

const IngredientMover = ({ 
    sections, 
    targetSection, 
    setTargetSection, 
    moveSelectedIngredients, 
    clearSelections 
}) => {
    return (
        <div className="movement-controls">
            <h3>Move Selected Ingredients</h3>
            <div className="control-row">
                <select
                    value={targetSection}
                    onChange={(e) => setTargetSection(e.target.value)}
                >
                    <option value="">Select Target Section</option>
                    {sections.map(section => (
                        <option key={section.id} value={section.id}>
                            {section.name}
                        </option>
                    ))}
                </select>
                <button
                    onClick={moveSelectedIngredients}
                    disabled={!targetSection}
                >
                    Move Selected
                </button>
                <button onClick={clearSelections}>
                    Clear Selection
                </button>
            </div>
        </div>
    );
};

export default IngredientMover;
// sectionGrid.js
import React from "react";

const SectionGrid = ({
    sections,
    getIngredientsForSection,
    getUncategorizedIngredients,
    selectedIngredients,
    toggleIngredientSelection,
    selectAllInSection,
    removeSection
}) => {
    // Get all available ingredients across all sections and uncategorized
    const allIngredients = [
        ...getUncategorizedIngredients(),
        ...sections.flatMap(section => getIngredientsForSection(section.id))
    ];

    // Filter out duplicate Uncategorized sections
    const uniqueSections = sections.filter((section, index, self) => {
        // Keep only the first occurrence of each section name (case-insensitive)
        return index === self.findIndex(s => 
            s.name.toLowerCase() === section.name.toLowerCase()
        );
    });

    return (
        <div className="organizer-content">
            {/* Left panel with all ingredients */}
            <div className="all-ingredients-panel">
                <h3>All Ingredients</h3>
                <div className="ingredient-list">
                    {allIngredients.length > 0 ? (
                        allIngredients.map(ingredient => (
                            <div
                                key={ingredient.id}
                                className={`ingredient-item ${selectedIngredients[ingredient.id] ? 'selected' : ''}`}
                                onClick={() => toggleIngredientSelection(ingredient.id)}
                            >
                                <input
                                    type="checkbox"
                                    checked={!!selectedIngredients[ingredient.id]}
                                    onChange={() => toggleIngredientSelection(ingredient.id)}
                                />
                                <span>{ingredient.name}</span>
                            </div>
                        ))
                    ) : (
                        <div className="empty-section">No ingredients available</div>
                    )}
                </div>
            </div>

            {/* Right panel with sections */}
            <div className="sections-panel">
                {uniqueSections.map(section => (
                    <div className="section-card" key={section.id}>
                        <div className="section-header">
                            <h3>{section.name}</h3>
                            <div className="section-actions">
                                <button onClick={() => selectAllInSection(section.id)}>
                                    Select All
                                </button>
                                {section.name.toLowerCase() !== "uncategorized" && (
                                    <button
                                        className="remove-section-btn"
                                        onClick={() => removeSection(section.id)}
                                    >
                                        ✕
                                    </button>
                                )}
                            </div>
                        </div>
                        <div className="ingredient-list">
                            {getIngredientsForSection(section.id).length > 0 ? (
                                getIngredientsForSection(section.id).map(ingredient => (
                                    <div
                                        key={ingredient.id}
                                        className={`ingredient-item ${selectedIngredients[ingredient.id] ? 'selected' : ''}`}
                                        onClick={() => toggleIngredientSelection(ingredient.id)}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={!!selectedIngredients[ingredient.id]}
                                            onChange={() => toggleIngredientSelection(ingredient.id)}
                                        />
                                        <span>{ingredient.name}</span>
                                    </div>
                                ))
                            ) : (
                                <div className="empty-section">No ingredients in this section</div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SectionGrid;
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const StoreOrganizerSimple = () => {
    const navigate = useNavigate();
    const [sections, setSections] = useState([]);
    const [ingredients, setIngredients] = useState([]);
    const [stores, setStores] = useState([]);
    const [selectedStore, setSelectedStore] = useState(null);
    const [newSectionName, setNewSectionName] = useState("");
    const [loading, setLoading] = useState(true);
    const [saveSuccess, setSaveSuccess] = useState(false);

    // Track which section an ingredient belongs to
    const [ingredientSections, setIngredientSections] = useState({});
    // Track which ingredients are selected for move operations
    const [selectedIngredients, setSelectedIngredients] = useState({});
    const [targetSection, setTargetSection] = useState("");

    // Add this function to your StoreOrganizerSimple component
    const debugIngredientMove = () => {
        console.log("=== DEBUG INGREDIENT MOVE ===");
        console.log("Current ingredient sections mapping:", ingredientSections);
        console.log("Selected ingredients:", selectedIngredients);
        console.log("Target section:", targetSection);

        // Check what ingredients should be in each section
        sections.forEach(section => {
            const sectionIngredients = ingredients.filter(ing =>
                ingredientSections[ing.id] === section.id
            );
            console.log(`Section ${section.name} (${section.id}) should have:`,
                sectionIngredients.map(ing => ing.name)
            );
        });

        // Check uncategorized
        const uncategorized = ingredients.filter(ing => !ingredientSections[ing.id]);
        console.log("Uncategorized should have:", uncategorized.map(ing => ing.name));
    }

    // Load all data
    useEffect(() => {
        const fetchStores = async () => {
            try {
                setLoading(true);
                const response = await fetch("http://127.0.0.1:5000/api/stores");
                const storesData = await response.json();
                setStores(storesData);

                if (storesData.length > 0) {
                    setSelectedStore(storesData[0].id);
                    fetchStoreData(storesData[0].id);
                } else {
                    await createDefaultStore();
                }
            } catch (error) {
                console.error("Error fetching stores:", error);
                setLoading(false);
            }
        };

        fetchStores();
    }, []);

    const fetchStoreData = async (storeId) => {
        try {
          setLoading(true);
          
          // Get sections
          const sectionsResponse = await fetch(`http://127.0.0.1:5000/api/stores/${storeId}/sections`);
          const sectionsData = await sectionsResponse.json();
          console.log("Fetched sections:", sectionsData);
          setSections(sectionsData);
          
          // Get all ingredients
          const ingredientsResponse = await fetch("http://127.0.0.1:5000/api/ingredients");
          const ingredientsData = await ingredientsResponse.json();
          console.log("Fetched ingredients:", ingredientsData);
          setIngredients(ingredientsData);
          
          // Get section mappings
          const mappingsResponse = await fetch(`http://127.0.0.1:5000/api/ingredient_sections?store_id=${storeId}`);
          const mappingsData = await mappingsResponse.json();
          console.log("Fetched mappings:", mappingsData);
          
          // Create ingredient to section mapping
          const sectionMap = {};
          mappingsData.forEach(mapping => {
            sectionMap[mapping.ingredient_id] = mapping.section_id;
          });
          
          console.log("Created section map:", sectionMap);
          setIngredientSections(sectionMap);
          setLoading(false);
        } catch (error) {
          console.error("Error fetching store data:", error);
          setLoading(false);
        }
      };

    // Create a default store if needed
    const createDefaultStore = async () => {
        try {
            const response = await fetch("http://127.0.0.1:5000/api/stores", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: "My Store",
                    sections: [
                        { name: "Produce", order: 0 },
                        { name: "Dairy", order: 1 },
                        { name: "Meat", order: 2 },
                        { name: "Bakery", order: 3 },
                        { name: "Frozen", order: 4 },
                        { name: "Canned Goods", order: 5 },
                        { name: "Uncategorized", order: 6 }
                    ]
                })
            });

            const data = await response.json();

            if (data.store_id) {
                const storesResponse = await fetch("http://127.0.0.1:5000/api/stores");
                const storesData = await storesResponse.json();
                setStores(storesData);

                if (storesData.length > 0) {
                    setSelectedStore(storesData[0].id);
                    fetchStoreData(storesData[0].id);
                }
            }
        } catch (error) {
            console.error("Error creating default store:", error);
            setLoading(false);
        }
    };

    // Handle store selection change
    const handleStoreChange = (e) => {
        const storeId = e.target.value;
        setSelectedStore(storeId);
        fetchStoreData(storeId);
    };

    // Add a new section
    const addNewSection = () => {
        if (!newSectionName.trim()) {
            alert("Please enter a section name");
            return;
        }

        // We'll add it to the UI immediately, but it won't have an ID until it's saved
        const newSection = {
            id: `temp-${Date.now()}`,
            name: newSectionName,
            order: sections.length
        };

        setSections([...sections, newSection]);
        setNewSectionName("");
    };

    // Remove a section
    const removeSection = (sectionId) => {
        // Remove the section
        setSections(sections.filter(s => s.id.toString() !== sectionId.toString()));

        // Update ingredient mappings
        const updatedSectionMap = { ...ingredientSections };

        // Remove all mappings to this section
        Object.keys(updatedSectionMap).forEach(ingredientId => {
            if (updatedSectionMap[ingredientId].toString() === sectionId.toString()) {
                delete updatedSectionMap[ingredientId];
            }
        });

        setIngredientSections(updatedSectionMap);
    };

    // Toggle ingredient selection
    const toggleIngredientSelection = (ingredientId) => {
        setSelectedIngredients(prev => ({
            ...prev,
            [ingredientId]: !prev[ingredientId]
        }));
    };

    // Select all ingredients in a section
    const selectAllInSection = (sectionId) => {
        const newSelected = { ...selectedIngredients };

        ingredients.forEach(ingredient => {
            if (ingredientSections[ingredient.id] === sectionId) {
                newSelected[ingredient.id] = true;
            }
        });

        setSelectedIngredients(newSelected);
    };

    // Clear all selections
    const clearSelections = () => {
        setSelectedIngredients({});
    };

    const moveSelectedIngredients = () => {
        if (!targetSection) {
          alert("Please select a target section");
          return;
        }
        
        const selectedIds = Object.keys(selectedIngredients).filter(id => selectedIngredients[id]);
        
        if (selectedIds.length === 0) {
          alert("Please select at least one ingredient to move");
          return;
        }
        
        console.log("Moving ingredients:", selectedIds);
        console.log("To section:", targetSection);
        
        // Create a new mapping object (always create a new object for state updates)
        const updatedSectionMap = { ...ingredientSections };
        
        selectedIds.forEach(ingredientId => {
          updatedSectionMap[ingredientId] = targetSection;
        });
        
        // Update the state
        setIngredientSections(updatedSectionMap);
        
        // Clear selections
        setSelectedIngredients({});
        setTargetSection("");
      }

    // Save organization to backend
// Update this function in the StoreOrganizerSimple component
const saveOrganization = async () => {
    try {
      // Format data for the API
      const sectionData = [];
      
      // Process regular sections
      for (const section of sections) {
        // Get ingredients for this section
        const sectionIngredients = ingredients.filter(ing => 
          String(ingredientSections[ing.id]) === String(section.id)
        );
        
        if (section.id.toString().startsWith('temp-') || sectionIngredients.length > 0) {
          sectionData.push({
            id: section.id.toString().startsWith('temp-') ? null : section.id,
            name: section.name,
            ingredients: sectionIngredients.map((ing, index) => ({
              id: ing.id,
              name: ing.name,
              order: index
            }))
          });
        }
      }
      
      // Handle uncategorized ingredients
      const uncategorizedIngredients = ingredients.filter(ing => !ingredientSections[ing.id]);
      
      if (uncategorizedIngredients.length > 0) {
        sectionData.push({
          id: null,
          name: "Uncategorized",
          ingredients: uncategorizedIngredients.map((ing, index) => ({
            id: ing.id,
            name: ing.name,
            order: index
          }))
        });
      }
      
      console.log("Saving organization with data:", sectionData);
      
      // Send to API
      const response = await fetch("http://127.0.0.1:5000/api/save_ingredient_sections", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          store_id: selectedStore,
          sections: sectionData
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to save organization: ${errorData.error || response.statusText}`);
      }
      
      // Show success message
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      
      // Refresh data to get updated mappings
      await fetchStoreData(selectedStore);
      
    } catch (error) {
      console.error("Error saving organization:", error);
      alert("Error saving organization: " + error.message);
    }
  };

    // Get ingredients for a specific section
// Get ingredients for a specific section
const getIngredientsForSection = (sectionId) => {
    // Log for debugging
    console.log(`Getting ingredients for section ${sectionId}`, 
      ingredients.filter(ing => ingredientSections[ing.id] === sectionId).map(i => i.name)
    );
    
    // IMPORTANT: Convert both to strings for comparison
    return ingredients.filter(ing => 
      String(ingredientSections[ing.id]) === String(sectionId)
    );
  };
  
  // Get uncategorized ingredients 
  const getUncategorizedIngredients = () => {
    return ingredients.filter(ing => !ingredientSections[ing.id]);
  };

    return (
        <div className="store-organizer-container">
            <div className="store-organizer-header">
                <h1>Store Section Organizer</h1>
                {saveSuccess && <div className="save-success-message">Organization saved successfully!</div>}
            </div>

            <div className="store-organizer-controls">
                <button onClick={debugIngredientMove} style={{ marginLeft: '10px' }}>
                    Debug Move
                </button>
                <button
                    className="back-btn"
                    onClick={() => navigate('/grocery-list')}
                >
                    ← Back to Grocery List
                </button>

                <div className="store-selector">
                    <label htmlFor="store-select">Select Store:</label>
                    <select
                        id="store-select"
                        value={selectedStore || ""}
                        onChange={handleStoreChange}
                    >
                        {stores.map(store => (
                            <option key={store.id} value={store.id}>{store.name}</option>
                        ))}
                    </select>
                </div>

                <div className="add-section-form">
                    <input
                        type="text"
                        value={newSectionName}
                        onChange={(e) => setNewSectionName(e.target.value)}
                        placeholder="New Section Name"
                    />
                    <button onClick={addNewSection}>Add Section</button>
                </div>

                <button className="save-organization-btn" onClick={saveOrganization}>
                    Save Organization
                </button>
            </div>

            {loading ? (
                <div className="loading">Loading sections and ingredients...</div>
            ) : (
                <div className="simple-organizer-layout">
                    {/* Ingredient Movement Controls */}
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

                    {/* Section Grid */}
                    <div className="section-grid">
                        {/* Uncategorized Section */}
                        <div className="section-card">
                            <div className="section-header">
                                <h3>Uncategorized</h3>
                                <button onClick={() => selectAllInSection(null)}>
                                    Select All
                                </button>
                            </div>
                            <div className="ingredient-list">
                                {getUncategorizedIngredients().length > 0 ? (
                                    getUncategorizedIngredients().map(ingredient => (
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
                                    <div className="empty-section">No uncategorized ingredients</div>
                                )}
                            </div>
                        </div>

                        {/* Regular Sections */}
                        {sections.map(section => (
                            <div className="section-card" key={section.id}>
                                <div className="section-header">
                                    <h3>{section.name}</h3>
                                    <div className="section-actions">
                                        <button onClick={() => selectAllInSection(section.id)}>
                                            Select All
                                        </button>
                                        <button
                                            className="remove-section-btn"
                                            onClick={() => removeSection(section.id)}
                                        >
                                            ✕
                                        </button>
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
            )}

            <div className="organizer-tip">
                <p>Tip: Check the ingredients you want to move, select a target section, and click "Move Selected".</p>
            </div>
        </div>
    );
};

export default StoreOrganizerSimple;
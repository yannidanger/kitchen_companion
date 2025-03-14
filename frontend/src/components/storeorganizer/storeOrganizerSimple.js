import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import StoreSelector from "./storeSelector";
import SectionManager from "./sectionManager";
import IngredientMover from "./ingredientMover";
import SaveButton from "./saveButton";
import SectionGrid from "./sectionGrid";
import DebugButton from "./debugButton";

const StoreOrganizerSimple = () => {
    const navigate = useNavigate();
    const [sections, setSections] = useState([]);
    const [ingredients, setIngredients] = useState([]);
    const [stores, setStores] = useState([]);
    const [selectedStore, setSelectedStore] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [ingredientSections, setIngredientSections] = useState({});
    const [selectedIngredients, setSelectedIngredients] = useState({});
    const [targetSection, setTargetSection] = useState("");
    const [newSectionName, setNewSectionName] = useState("");


    const createDefaultStore = useCallback(async () => {
        try {
            const response = await fetch("http://127.0.0.1:5000/api/stores", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
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
    }, []); // ✅ Now it's stable

    const fetchStores = useCallback(async () => {
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
    }, [createDefaultStore]); // ✅ Now includes createDefaultStore

    useEffect(() => {
        fetchStores();
    }, [fetchStores]); // ✅ Warning should be gone now

    const fetchStoreData = async (storeId) => {
        try {
            setLoading(true);
            const sectionsResponse = await fetch(`http://127.0.0.1:5000/api/stores/${storeId}/sections`);
            if (!sectionsResponse.ok) {
                throw new Error(`Failed to fetch sections: ${sectionsResponse.statusText}`);
            }
            const sectionsData = await sectionsResponse.json();

            // Filter out duplicate sections (keeping only the first occurrence of each name)
            const uniqueSections = sectionsData.filter((section, index, self) =>
                index === self.findIndex(s => s.name.toLowerCase() === section.name.toLowerCase())
            );

            setSections(uniqueSections);

            const ingredientsResponse = await fetch("http://127.0.0.1:5000/api/ingredients");
            if (!ingredientsResponse.ok) {
                throw new Error(`Failed to fetch ingredients: ${ingredientsResponse.statusText}`);
            }
            const ingredientsData = await ingredientsResponse.json();
            setIngredients(ingredientsData);

            const mappingsResponse = await fetch(`http://127.0.0.1:5000/api/ingredient_sections?store_id=${storeId}`);
            if (!mappingsResponse.ok) {
                throw new Error(`Failed to fetch ingredient mappings: ${mappingsResponse.statusText}`);
            }
            const mappingsData = await mappingsResponse.json();

            const sectionMap = {};
            mappingsData.forEach(mapping => {
                sectionMap[mapping.ingredient_id] = mapping.section_id;
            });

            setIngredientSections(sectionMap);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching store data:", error);
            setLoading(false);
        }
    };

    const handleStoreChange = (storeId) => {
        setSelectedStore(storeId);
        fetchStoreData(storeId);
    };

    // In storeOrganizerSimple.js, modify the addNewSection function:
    const addNewSection = (name) => {
        if (!name.trim()) {
            alert("Please enter a section name");
            return;
        }

        // Standardize section name formatting
        const sectionName = name.trim()
            .replace(/\s+/g, ' ')  // Replace multiple spaces with single space
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');

        // Check for duplicates (case-insensitive)
        const isDuplicate = sections.some(
            section => section.name.toLowerCase() === sectionName.toLowerCase()
        );

        if (isDuplicate) {
            alert(`A section named "${sectionName}" already exists`);
            return;
        }

        const newSection = {
            id: `temp-${Date.now()}`,
            name: sectionName,
            order: sections.length
        };

        setSections([...sections, newSection]);
        setNewSectionName(""); // Reset the input field
    };

    const removeSection = (sectionId) => {
        setSections(sections.filter(s => String(s.id) !== String(sectionId)));

        // When removing a section, update ingredientSections to remove mappings
        const updatedSectionMap = { ...ingredientSections };
        Object.keys(updatedSectionMap).forEach(ingredientId => {
            if (String(updatedSectionMap[ingredientId]) === String(sectionId)) {
                delete updatedSectionMap[ingredientId];
            }
        });

        setIngredientSections(updatedSectionMap);
    };

    const toggleIngredientSelection = (ingredientId) => {
        setSelectedIngredients(prev => ({
            ...prev,
            [ingredientId]: !prev[ingredientId]
        }));
    };

    const selectAllInSection = (sectionId) => {
        const newSelected = { ...selectedIngredients };

        ingredients.forEach(ingredient => {
            if (ingredientSections[ingredient.id] === sectionId) {
                newSelected[ingredient.id] = true;
            }
        });

        setSelectedIngredients(newSelected);
    };

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

        const updatedSectionMap = { ...ingredientSections };

        selectedIds.forEach(ingredientId => {
            // Update the mapping to the new section
            updatedSectionMap[ingredientId] = targetSection;
        });

        setIngredientSections(updatedSectionMap);
        setSelectedIngredients({});
        setTargetSection("");
    };

    const saveOrganization = async () => {
        try {
            const sectionData = [];

            for (const section of sections) {
                const sectionIngredients = ingredients.filter(ing =>
                    String(ingredientSections[ing.id]) === String(section.id)
                );

                sectionData.push({
                    id: section.id.toString().startsWith('temp-') ? null : section.id,
                    name: section.name,
                    ingredients: sectionIngredients.map(ing => ({
                        id: ing.id,
                        name: ing.name
                    }))
                });
            }

            // Add uncategorized ingredients
            const uncategorizedIngredients = ingredients.filter(ing => !ingredientSections[ing.id]);

            if (uncategorizedIngredients.length > 0) {
                sectionData.push({
                    name: "Uncategorized",
                    ingredients: uncategorizedIngredients.map(ing => ({
                        id: ing.id,
                        name: ing.name
                    }))
                });
            }

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

            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 3000);

            await fetchStoreData(selectedStore);

        } catch (error) {
            console.error("Error saving organization:", error);
            alert("Error saving organization: " + error.message);
        }
    };

    const getIngredientsForSection = (sectionId) => {
        // Return ONLY ingredients mapped to this specific section
        return ingredients.filter(ing =>
            String(ingredientSections[ing.id]) === String(sectionId)
        );
    };

    const getUncategorizedIngredients = () => {
        // Return ONLY ingredients with no section mapping
        return ingredients.filter(ing => !ingredientSections[ing.id]);
    };

    // Add this function to storeOrganizerSimple.js
    const createNewStore = async (storeName) => {
        try {
            const response = await fetch("http://127.0.0.1:5000/api/stores", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: storeName,
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
                // Refresh the store list
                fetchStores();
            }
        } catch (error) {
            console.error("Error creating store:", error);
            alert("Failed to create store. Please try again.");
        }
    };

    const debugIngredientMove = () => {
        console.log("=== DEBUG INGREDIENT MOVE ===");
        console.log("Current ingredient sections mapping:", ingredientSections);
        console.log("Selected ingredients:", selectedIngredients);
        console.log("Target section:", targetSection);

        sections.forEach(section => {
            const sectionIngredients = ingredients.filter(ing =>
                ingredientSections[ing.id] === section.id
            );
            console.log(`Section ${section.name} (${section.id}) should have:`,
                sectionIngredients.map(ing => ing.name)
            );
        });

        const uncategorized = ingredients.filter(ing => !ingredientSections[ing.id]);
        console.log("Uncategorized should have:", uncategorized.map(ing => ing.name));
    };

    return (
        <div className="store-organizer-container">
            <div className="store-organizer-header">
                <h1>Store Section Organizer</h1>
                {saveSuccess && <div className="save-success-message">Organization saved successfully!</div>}
            </div>

            <div className="store-organizer-controls">
                <DebugButton onClick={debugIngredientMove} />

                <button
                    className="back-btn"
                    onClick={() => navigate('/grocery-list')}
                >
                    ← Back to Grocery List
                </button>

                <StoreSelector
                    stores={stores}
                    selectedStore={selectedStore}
                    onChange={handleStoreChange}
                    onCreateStore={createNewStore}
                />

                <SectionManager
                    newSectionName={newSectionName}
                    setNewSectionName={setNewSectionName}
                    addNewSection={addNewSection}
                />

                <SaveButton
                    saveSuccess={saveSuccess}
                    onClick={saveOrganization}
                />
            </div>

            {loading ? (
                <div className="loading">Loading sections and ingredients...</div>
            ) : (
                <div className="simple-organizer-layout">
                    <IngredientMover
                        sections={sections}
                        targetSection={targetSection}
                        setTargetSection={setTargetSection}
                        moveSelectedIngredients={moveSelectedIngredients}
                        clearSelections={clearSelections}
                        selectedIngredients={selectedIngredients} // Add this prop
                    />

                    <SectionGrid
                        sections={sections}
                        getIngredientsForSection={getIngredientsForSection}
                        getUncategorizedIngredients={getUncategorizedIngredients}
                        selectedIngredients={selectedIngredients}
                        toggleIngredientSelection={toggleIngredientSelection}
                        selectAllInSection={selectAllInSection}
                        removeSection={removeSection}
                    />
                </div>
            )}

            <div className="organizer-tip">
                <p>Tip: Check the ingredients you want to move, select a target section, and click "Move Selected".</p>
            </div>
        </div>
    );
};

export default StoreOrganizerSimple;
// StoreOrganizer.js
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

const SortableIngredient = ({ ingredient, index }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({
    id: `ingredient-${ingredient.id}`,
    data: {
      type: 'ingredient',
      ingredient
    }
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    cursor: 'grab',
    userSelect: 'none'
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`ingredient-item ${isDragging ? 'dragging' : ''}`}
      {...attributes}
      {...listeners}
      data-id={ingredient.id}
    >
      {ingredient.name}
    </div>
  );
};

const StoreOrganizer = () => {
  const navigate = useNavigate();
  const [sections, setSections] = useState([]);
  const [, setIngredients] = useState([]);
  const [stores, setStores] = useState([]);
  const [selectedStore, setSelectedStore] = useState(null);
  const [newSectionName, setNewSectionName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const [activeDragData, setActiveDragData] = useState(null);
  const [activeDroppableId, setActiveDroppableId] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const fetchSectionsRef = React.useRef(null);
  const createDefaultStoreRef = React.useRef(null);
  const fetchDataRef = React.useRef(null);

  // Create wrapper functions
  const fetchSections = useCallback(async (storeId) => {
    return fetchSectionsRef.current?.(storeId);
  }, []);

  const createDefaultStore = useCallback(async () => {
    return createDefaultStoreRef.current?.();
  }, []);

  const fetchData = useCallback(async () => {
    return fetchDataRef.current?.();
  }, []);

  // Set up implementations with useEffect
  useEffect(() => {
    fetchSectionsRef.current = async (storeId) => {
      try {
        const sectionsResponse = await fetch(`http://127.0.0.1:5000/api/stores/${storeId}/sections`);
        const sectionsData = await sectionsResponse.json();

        // Initialize sections with empty ingredient arrays
        const sectionsWithIngredients = sectionsData.map(section => ({
          ...section,
          ingredients: []
        }));

        setSections(sectionsWithIngredients);

        // Fetch ingredients
        const ingredientsResponse = await fetch("http://127.0.0.1:5000/api/ingredients");
        const ingredientsData = await ingredientsResponse.json();

        if (ingredientsData.length === 0) {
          setSections(sectionsWithIngredients);
          setIngredients([]);
          setLoading(false);
          return; // Early return if no ingredients to process
        }

        // Fetch ingredient section mappings
        const mappingsResponse = await fetch(`http://127.0.0.1:5000/api/ingredient_sections?store_id=${storeId}`);
        const mappingsData = await mappingsResponse.json();

        // Organize ingredients into sections
        const sectionMap = {};
        sectionsWithIngredients.forEach(section => {
          sectionMap[section.id] = section;
        });

        // Add a default "Uncategorized" section
        let uncategorizedSection = {
          id: "uncategorized",
          name: "Uncategorized",
          ingredients: []
        };

        // Assign ingredients to their sections based on mappings
        ingredientsData.forEach(ingredient => {
          const mapping = mappingsData.find(m => m.ingredient_id === ingredient.id);

          if (mapping && sectionMap[mapping.section_id]) {
            sectionMap[mapping.section_id].ingredients.push(ingredient);
          } else {
            uncategorizedSection.ingredients.push(ingredient);
          }
        });

        // Update sections array with assigned ingredients
        const updatedSections = [...Object.values(sectionMap)];

        // Add uncategorized section if it has ingredients
        if (uncategorizedSection.ingredients.length > 0) {
          updatedSections.push(uncategorizedSection);
        }

        setSections(updatedSections);
        setIngredients(ingredientsData);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching sections and ingredients:", error);
        setLoading(false);
      }
    };

    // Implement createDefaultStore
    createDefaultStoreRef.current = async () => {
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
          // Fetch stores again to get the new store
          const storesResponse = await fetch("http://127.0.0.1:5000/api/stores");
          const storesData = await storesResponse.json();
          setStores(storesData);

          // Set the first store as selected
          if (storesData.length > 0) {
            setSelectedStore(storesData[0].id);
            await fetchSections(storesData[0].id);
          }
        }

        setLoading(false);
      } catch (error) {
        console.error("Error creating default store:", error);
        setLoading(false);
      }
    };

    // Implement fetchData
    fetchDataRef.current = async () => {
      try {
        setLoading(true);

        // Fetch stores
        const storesResponse = await fetch("http://127.0.0.1:5000/api/stores");
        const storesData = await storesResponse.json();
        setStores(storesData);

        if (storesData.length > 0) {
          setSelectedStore(storesData[0].id);

          // Fetch sections for the selected store
          await fetchSections(storesData[0].id);
        } else {
          // Create a default store if none exists
          await createDefaultStore();
        }
      } catch (error) {
        console.error("Error fetching data:", error);
        setLoading(false);
      }
    };
  }, []);

  // Call fetchData on component mount
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleStoreChange = (e) => {
    const storeId = e.target.value;
    setSelectedStore(storeId);
    fetchSections(storeId);
  };

  const addNewSection = () => {
    if (!newSectionName.trim()) {
      alert("Please enter a section name");
      return;
    }

    // Create new section locally first
    const newSection = {
      id: `temp-${Date.now()}`, // Temporary ID until saved
      name: newSectionName,
      order: sections.length,
      ingredients: []
    };

    setSections([...sections, newSection]);
    setNewSectionName("");
  };

  useEffect(() => {
    console.log("Sections state after update:", sections);
  }, [sections]);

  const removeSection = (sectionId) => {
    // Get the section
    const section = sections.find(s => s.id.toString() === sectionId.toString());

    if (!section) return;

    // Make a copy of sections
    const newSections = [...sections];

    // If section has ingredients, move them to uncategorized
    let uncategorizedIndex = newSections.findIndex(s => s.id === "uncategorized");
    let uncategorized;

    if (uncategorizedIndex === -1) {
      // Create uncategorized section if it doesn't exist
      uncategorized = {
        id: "uncategorized",
        name: "Uncategorized",
        ingredients: []
      };

      // Filter out the section to remove and add uncategorized
      setSections([
        ...newSections.filter(s => s.id.toString() !== sectionId.toString()),
        uncategorized
      ]);
    } else {
      // Get a reference to the uncategorized section
      uncategorized = { ...newSections[uncategorizedIndex] };

      // Create a new array for its ingredients
      uncategorized.ingredients = [...uncategorized.ingredients];

      // If the section to remove has ingredients, add them to uncategorized
      if (section.ingredients.length > 0) {
        uncategorized.ingredients = [...uncategorized.ingredients, ...section.ingredients];
      }

      // Update the uncategorized section in the newSections array
      newSections[uncategorizedIndex] = uncategorized;

      // Remove the section to delete
      setSections(newSections.filter(s => s.id.toString() !== sectionId.toString()));
    }
  };

  const saveOrganization = async () => {
    try {
      // Prepare the data
      const sectionData = sections
        .filter(section => section.id !== "uncategorized")
        .map(section => ({
          id: section.id.toString().startsWith('temp-') ? null : section.id,
          name: section.name,
          ingredients: section.ingredients.map((ingredient, index) => ({
            id: ingredient.id,
            name: ingredient.name,
            order: index
          }))
        }));

      // Add uncategorized section if it exists
      const uncategorizedSection = sections.find(s => s.id === "uncategorized");
      if (uncategorizedSection && uncategorizedSection.ingredients.length > 0) {
        sectionData.push({
          id: null,
          name: "Uncategorized",
          ingredients: uncategorizedSection.ingredients.map((ingredient, index) => ({
            id: ingredient.id,
            name: ingredient.name,
            order: index
          }))
        });
      }

      // Send to the backend
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
        throw new Error("Failed to save organization");
      }

      // Show success message
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);

    } catch (error) {
      console.error("Error saving organization:", error);
      alert("Error saving organization: " + error.message);
    }
  };

  const handleDragStart = (event) => {
    const { active } = event;
    setActiveId(active.id);
    setActiveDragData(active.data.current?.ingredient || null);
  };

  const handleDragOver = (event) => {
    // eslint-disable-next-line no-unused-vars
    const { active, over } = event;

    if (!over) {
      setActiveDroppableId(null);
      return;
    }

    // If we're over a section or a droppable element
    if (over.id.startsWith('section-') || over.data?.current?.droppable) {
      const sectionId = over.id.startsWith('section-')
        ? over.id
        : findContainer(over.id);

      if (sectionId) {
        console.log("Hovering over section:", sectionId);
        setActiveDroppableId(sectionId);
      } else {
        setActiveDroppableId(null);
      }
    } else {
      setActiveDroppableId(null);
    }
  };

  const handleDragEnd = (event) => {
    console.log("handleDragEnd starting with sections:", JSON.stringify(sections.map(s => ({
      id: s.id,
      name: s.name,
      ingredientCount: s.ingredients.length
    }))));

    const { active, over } = event;

    setActiveDroppableId(null);
    setActiveId(null);
    setActiveDragData(null);

    if (!active || !over) {
      console.log("No active or over element in drag end");
      return;
    }

    console.log("Active ID:", active.id);
    console.log("Over ID:", over.id);

    // Extract the ingredient ID and data
    const ingredientId = active.id.replace('ingredient-', '');
    const ingredientData = active.data.current?.ingredient;

    if (!ingredientData) {
      console.log("No ingredient data found");
      return;
    }

    // Create a completely new sections array
    const newSections = JSON.parse(JSON.stringify(sections));

    // Find source section and ingredient
    let sourceSectionIndex = -1;
    let sourceIngredientIndex = -1;

    // Find which section contains this ingredient
    for (let i = 0; i < newSections.length; i++) {
      const index = newSections[i].ingredients.findIndex(
        ing => ing.id.toString() === ingredientId
      );
      if (index !== -1) {
        sourceSectionIndex = i;
        sourceIngredientIndex = index;
        break;
      }
    }

    if (sourceSectionIndex === -1 || sourceIngredientIndex === -1) {
      console.log("Source ingredient not found");
      return;
    }

    // Get the target section
    let targetSectionIndex = -1;

    if (over.id.startsWith('section-')) {
      // Direct drop on section
      const targetSectionId = over.id.replace('section-', '');
      targetSectionIndex = newSections.findIndex(
        s => s.id.toString() === targetSectionId
      );
    } else if (over.id.startsWith('ingredient-')) {
      // Drop on another ingredient - find its section
      const overIngredientId = over.id.replace('ingredient-', '');

      for (let i = 0; i < newSections.length; i++) {
        const index = newSections[i].ingredients.findIndex(
          ing => ing.id.toString() === overIngredientId
        );
        if (index !== -1) {
          targetSectionIndex = i;
          break;
        }
      }
    }

    if (targetSectionIndex === -1) {
      console.log("Target section not found");
      return;
    }

    // Get the ingredient to move
    const ingredientToMove = newSections[sourceSectionIndex].ingredients[sourceIngredientIndex];

    // Remove from source
    newSections[sourceSectionIndex].ingredients.splice(sourceIngredientIndex, 1);

    // Add to target based on where we dropped
    if (over.id.startsWith('ingredient-')) {
      const overIngredientId = over.id.replace('ingredient-', '');
      const targetIngredientIndex = newSections[targetSectionIndex].ingredients.findIndex(
        ing => ing.id.toString() === overIngredientId
      );

      if (targetIngredientIndex !== -1) {
        // Insert at specific position
        newSections[targetSectionIndex].ingredients.splice(
          targetIngredientIndex, 0, ingredientToMove
        );
      } else {
        // Fallback to end of section
        newSections[targetSectionIndex].ingredients.push(ingredientToMove);
      }
    } else {
      // Add to end of section
      newSections[targetSectionIndex].ingredients.push(ingredientToMove);
    }

    console.log("Updated sections structure:", newSections);
    console.log("Setting sections to:", JSON.stringify(newSections.map(s => ({
      id: s.id,
      name: s.name,
      ingredientCount: s.ingredients.length
    }))));

    // Update state with completely new sections array
    setSections(newSections);
  };

  const findContainer = (id) => {
    console.debug("Finding container for id:", id);

    // If the ID is a section ID
    if (id && id.startsWith('section-')) {
      return id;
    }

    // For ingredients, find which section they're in
    if (id && id.startsWith('ingredient-')) {
      const ingredientId = id.replace('ingredient-', '');
      for (const section of sections) {
        const foundIngredient = section.ingredients.find(ingredient =>
          ingredient.id && ingredient.id.toString() === ingredientId
        );
        if (foundIngredient) {
          return `section-${section.id}`;
        }
      }
    }

    return null;
  };

  // Helper function to find an ingredient's index within a section
  const findIndex = (containerId, itemId) => {
    const sectionId = containerId.replace('section-', '');
    const section = sections.find(s => s.id.toString() === sectionId);
    if (!section) return -1;

    if (itemId.startsWith('ingredient-')) {
      const ingredientId = itemId.replace('ingredient-', '');
      return section.ingredients.findIndex(i => i.id.toString() === ingredientId);
    }

    return -1;

  };

  // Helper function to get an ingredient by ID
  const getIngredientById = (id) => {
    if (id.startsWith('ingredient-')) {
      const ingredientId = id.replace('ingredient-', '');
      for (const section of sections) {
        const ingredient = section.ingredients.find(i => i.id.toString() === ingredientId);
        if (ingredient) return ingredient;
      }
    }
    return null;
  };

  // Generate a unique key for SortableContext to force re-renders
  const getSectionKey = (sectionId, count) => `section-${sectionId}-${count}`;

  // Add this before the return statement
  const inspectSections = () => {
    console.log("SECTION INSPECTION:");
    sections.forEach(section => {
      console.log(`Section ${section.name} (${section.id}): ${section.ingredients.length} ingredients`);
      const ingredientIds = section.ingredients.map(i => i.id);
      console.log("Ingredient IDs:", ingredientIds);

      // Check for duplicates
      const uniqueIds = new Set(ingredientIds);
      if (uniqueIds.size !== ingredientIds.length) {
        console.error("⚠️ DUPLICATE INGREDIENTS DETECTED");
      }
    });
  };

  // Add this button to your debug section
  <button onClick={inspectSections}>
    Inspect Sections
  </button>


  return (
    <div className="store-organizer-container">
      <div className="store-organizer-header">
        <h1>Store Section Organizer</h1>
        {saveSuccess && <div className="save-success-message">Organization saved successfully!</div>}
      </div>

      <div className="store-organizer-controls">
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
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <div className="organizer-layout">
            <div className="ingredients-panel">
              <h2>All Ingredients</h2>
              <SortableContext
                id="all-ingredients"
                items={sections
                  .find(s => s.id === "uncategorized")?.ingredients.map(i => `ingredient-${i.id}`) || []}
                strategy={verticalListSortingStrategy}
              >
                <div className="ingredient-list all-ingredients">
                  {sections.find(s => s.id === "uncategorized")?.ingredients.map((ingredient, index) => (
                    <SortableIngredient
                      key={`uncategorized-ingredient-${ingredient.id}`} // Changed this line
                      ingredient={ingredient}
                      index={index}
                    />
                  ))}
                  {!sections.find(s => s.id === "uncategorized") ||
                    sections.find(s => s.id === "uncategorized").ingredients.length === 0 ? (
                    <div className="empty-ingredients">
                      No uncategorized ingredients
                    </div>
                  ) : null}
                </div>
              </SortableContext>
            </div>

            <div className="sections-container">
              {sections.filter(section => section.id !== "uncategorized").map(section => (
                <div
                  className={`section-card ${activeDroppableId === `section-${section.id}` ? 'drop-target' : ''}`}
                  key={section.id}
                  id={`section-${section.id}`}
                >
                  <div className="section-header">
                    <h3>{section.name}</h3>
                    <button
                      className="remove-section-btn"
                      onClick={() => removeSection(section.id)}
                    >
                      ✕
                    </button>
                  </div>

                  <SortableContext
                    key={getSectionKey(section.id, section.ingredients.length)}
                    id={`section-${section.id}`}
                    items={section.ingredients.map(i => `ingredient-${i.id}`)}
                    strategy={verticalListSortingStrategy}
                  >
                    <div
                      className="ingredient-list"
                      data-section-id={section.id}
                    >
                      {section.ingredients.length > 0 ? (
                        section.ingredients.map((ingredient, index) => (
                          <SortableIngredient
                            key={`${section.id}-ingredient-${ingredient.id}`} // Make sure this is consistent
                            ingredient={ingredient}
                            index={index}
                          />
                        ))
                      ) : (
                        <div className="empty-section">
                          Drag ingredients here
                        </div>
                      )}
                    </div>
                  </SortableContext>
                </div>
              ))}
            </div>
          </div>

          <DragOverlay>
            {activeId && activeDragData ? (
              <div className="ingredient-item dragging">
                {activeDragData.name}
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      )}

      <div className="organizer-tip">
        <p>Tip: Drag and drop ingredients between sections to organize your grocery list.</p>
      </div>
      {/* Add this at the end of your component, before the closing </div> */}
      <div style={{ marginTop: '20px', padding: '10px', background: '#f0f0f0', borderRadius: '4px' }}>
        <h3>Debug Info:</h3>
        <button onClick={() => console.log("Current sections:", sections)}>
          Log Sections State
        </button>
        <div style={{ fontSize: '12px', marginTop: '10px' }}>
          Active ID: {activeId || 'none'}
        </div>
      </div>
    </div>
  );
};

export default StoreOrganizer;
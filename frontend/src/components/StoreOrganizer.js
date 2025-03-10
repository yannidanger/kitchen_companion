// In StoreOrganizer.js
// Modify the code as follows:

import React, { useState, useEffect, useCallback } from "react";
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";

function StoreOrganizer() {
  const [sections, setSections] = useState([]);
  const [, setIngredients] = useState([]); // Only using the setter
  const [stores, setStores] = useState([]);
  const [selectedStore, setSelectedStore] = useState(null);
  const [newSectionName, setNewSectionName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Wrap fetchSections in useCallback
  const fetchSections = useCallback(async (storeId) => {
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
  }, []);
  
  // Define fetchData after fetchSections
  const fetchData = useCallback(async () => {
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
        setLoading(false);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      setLoading(false);
    }
  }, [fetchSections]);
  
  // Use fetchData in useEffect
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  // Rest of the component unchanged...
  
  const handleStoreChange = (e) => {
    const storeId = e.target.value;
    setSelectedStore(storeId);
    fetchSections(storeId);
  };
  
  const handleDragEnd = (result) => {
    const { source, destination } = result;
    
    // Dropped outside a droppable area
    if (!destination) return;
    
    // Moved within the same section
    if (source.droppableId === destination.droppableId) {
      const sectionId = source.droppableId;
      const section = sections.find(s => s.id.toString() === sectionId);
      
      if (section) {
        const newIngredients = [...section.ingredients];
        const [removed] = newIngredients.splice(source.index, 1);
        newIngredients.splice(destination.index, 0, removed);
        
        const newSections = sections.map(s => {
          if (s.id.toString() === sectionId) {
            return { ...s, ingredients: newIngredients };
          }
          return s;
        });
        
        setSections(newSections);
      }
    } 
    // Moved to a different section
    else {
      const sourceSection = sections.find(s => s.id.toString() === source.droppableId);
      const destSection = sections.find(s => s.id.toString() === destination.droppableId);
      
      if (sourceSection && destSection) {
        // Copy the arrays
        const sourceIngredients = [...sourceSection.ingredients];
        const destIngredients = [...destSection.ingredients];
        
        // Remove from source and add to destination
        const [removed] = sourceIngredients.splice(source.index, 1);
        destIngredients.splice(destination.index, 0, removed);
        
        // Update the sections
        const newSections = sections.map(s => {
          if (s.id.toString() === source.droppableId) {
            return { ...s, ingredients: sourceIngredients };
          }
          if (s.id.toString() === destination.droppableId) {
            return { ...s, ingredients: destIngredients };
          }
          return s;
        });
        
        setSections(newSections);
      }
    }
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
  
  const removeSection = (sectionId) => {
    // Get the section
    const section = sections.find(s => s.id.toString() === sectionId.toString());
    
    if (!section) return;
    
    // If section has ingredients, move them to uncategorized
    let uncategorized = sections.find(s => s.id === "uncategorized");
    
    if (section.ingredients.length > 0) {
      if (!uncategorized) {
        // Create uncategorized section if it doesn't exist
        uncategorized = {
          id: "uncategorized",
          name: "Uncategorized",
          ingredients: []
        };
        
        // Add to sections
        setSections([...sections.filter(s => s.id.toString() !== sectionId.toString()), uncategorized]);
      } else {
        // Update sections without the removed one
        setSections(sections.filter(s => s.id.toString() !== sectionId.toString()));
      }
      
      // Move ingredients to uncategorized
      uncategorized.ingredients = [...uncategorized.ingredients, ...section.ingredients];
    } else {
      // Just remove the section
      setSections(sections.filter(s => s.id.toString() !== sectionId.toString()));
    }
  };
  
  const saveOrganization = async () => {
    try {
      // Prepare the data
      const sectionData = sections.map(section => ({
        id: section.id === "uncategorized" ? null : section.id,
        name: section.name,
        ingredients: section.ingredients.map((ingredient, index) => ({
          id: ingredient.id,
          name: ingredient.name,
          order: index
        }))
      }));
      
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
  
  return (
    <div className="store-organizer-container">
      <div className="store-organizer-header">
        <h1>Store Section Organizer</h1>
        {saveSuccess && <div className="save-success-message">Organization saved successfully!</div>}
      </div>
      
      <div className="store-organizer-controls">
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
        <DragDropContext onDragEnd={handleDragEnd}>
          <div className="sections-container">
            {sections.map(section => (
              <div className="section-card" key={section.id}>
                <div className="section-header">
                  <h3>{section.name}</h3>
                  {section.id !== "uncategorized" && (
                    <button 
                      className="remove-section-btn"
                      onClick={() => removeSection(section.id)}
                    >
                      ✕
                    </button>
                  )}
                </div>
                
                <Droppable droppableId={section.id.toString()}>
                  {(provided, snapshot) => (
                    <div
                      className={`ingredient-list ${snapshot.isDraggingOver ? 'dragging-over' : ''}`}
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                    >
                      {section.ingredients.length > 0 ? (
                        section.ingredients.map((ingredient, index) => (
                          <Draggable 
                            key={ingredient.id} 
                            draggableId={ingredient.id.toString()} 
                            index={index}
                          >
                            {(provided, snapshot) => (
                              <div
                                className={`ingredient-item ${snapshot.isDragging ? 'dragging' : ''}`}
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                              >
                                {ingredient.name}
                              </div>
                            )}
                          </Draggable>
                        ))
                      ) : (
                        <div className="empty-section">
                          Drag ingredients here
                        </div>
                      )}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            ))}
          </div>
        </DragDropContext>
      )}
      
      <div className="organizer-tip">
        <p>Tip: Drag and drop ingredients between sections to organize your grocery list.</p>
      </div>
    </div>
  );
}

export default StoreOrganizer;
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";

function GroceryListView() {
  const { planId } = useParams(); // For viewing an existing saved plan's groceries
  const location = useLocation(); // For previewing groceries without saving
  const navigate = useNavigate();

  const [groceryList, setGroceryList] = useState([]);
  const [planDetails, setPlanDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPrinting, setIsPrinting] = useState(false);
  const [isReordering, setIsReordering] = useState(false);
  const [selectedStore, setSelectedStore] = useState(null);
  const [detailedView, setDetailedView] = useState(false);
  const [useUsda, setUseUsda] = useState(true); // New state for USDA integration toggle

  // Define fetch functions with useCallback to avoid dependency issues
  const fetchGroceryListForPlan = useCallback(async (id) => {
    try {
      setLoading(true);

      // First, fetch plan details
      const planResponse = await fetch(`http://127.0.0.1:5000/api/weekly_plan/${id}`);
      if (!planResponse.ok) {
        throw new Error("Failed to fetch plan details");
      }

      const planData = await planResponse.json();
      setPlanDetails({
        ...planData,
        isTemporary: false
      });

      // Then fetch grocery list with USDA option
      const groceryResponse = await fetch(`http://127.0.0.1:5000/api/grocery_list?weekly_plan_id=${id}&use_usda=${useUsda}`);
      if (!groceryResponse.ok) {
        throw new Error("Failed to fetch grocery list");
      }

      const groceryData = await groceryResponse.json();
      console.log("Raw grocery list data:", groceryData.grocery_list);

      console.log("=== DETAILED API INSPECTION ===");
      groceryData.grocery_list.forEach(section => {
        console.log(`Section: ${section.section}`);
        section.items.forEach(item => {
          console.log(`Item: ${item.name}`, {
            size_exists: 'size' in item,
            descriptor_exists: 'descriptor' in item,
            additional_descriptor_exists: 'additional_descriptor' in item,
            preparation_exists: 'preparation' in item,
            size: item.size,
            descriptor: item.descriptor,
            additional_descriptor: item.additional_descriptor,
            preparation: item.preparation
          });
        });
      });

      // Sort the grocery list by section order if available
      const sortedList = groceryData.grocery_list.sort((a, b) => {
        // Put Uncategorized at the end
        if (a.section === "Uncategorized") return 1;
        if (b.section === "Uncategorized") return -1;

        // Sort by order if available
        if (a.order !== undefined && b.order !== undefined) {
          return a.order - b.order;
        }

        // Fall back to alphabetical order
        return a.section.localeCompare(b.section);
      });

      setGroceryList(sortedList || []);
      console.log("Grocery list data:", sortedList);
      setLoading(false);

    } catch (err) {
      console.error("Error fetching grocery list:", err);
      setError(err.message);
      setLoading(false);
    }
  }, [useUsda]);

  // Update the generateGroceryListFromMeals function similarly
  const generateGroceryListFromMeals = useCallback(async (meals) => {
    try {
      setLoading(true);

      // Generate grocery list from meals array without saving the plan
      const response = await fetch(`http://127.0.0.1:5000/api/generate_grocery_list`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          meals: meals,
          use_usda: useUsda // Add USDA flag
        })
      });

      if (!response.ok) {
        throw new Error("Failed to generate grocery list");
      }

      const data = await response.json();

      // Sort the grocery list by section order if available
      const sortedList = data.grocery_list.sort((a, b) => {
        // Put Uncategorized at the end
        if (a.section === "Uncategorized") return 1;
        if (b.section === "Uncategorized") return -1;

        // Sort by order if available
        if (a.order !== undefined && b.order !== undefined) {
          return a.order - b.order;
        }

        // Fall back to alphabetical order
        return a.section.localeCompare(b.section);
      });

      setGroceryList(sortedList || []);
      setLoading(false);

    } catch (err) {
      console.error("Error generating grocery list:", err);
      setError(err.message);
      setLoading(false);
    }
  }, [useUsda]);

  // Initial load effect
  useEffect(() => {
    if (planId) {
      // If planId is provided, fetch the grocery list for this saved plan
      fetchGroceryListForPlan(planId);
    } else if (location.state && location.state.meals) {
      // If we have meals data in location state, generate grocery list without saving
      generateGroceryListFromMeals(location.state.meals);
      setPlanDetails({
        name: location.state.planName || "Unnamed Meal Plan",
        isTemporary: true
      });
    } else {
      // No plan ID or meals data
      setError("No meal plan data found.");
      setLoading(false);
    }
  }, [planId, location.state, fetchGroceryListForPlan, generateGroceryListFromMeals]);

  // Refetch when USDA mode changes
  useEffect(() => {
    if (planId) {
      fetchGroceryListForPlan(planId);
    } else if (location.state && location.state.meals) {
      generateGroceryListFromMeals(location.state.meals);
    }
  }, [useUsda, planId, location.state, fetchGroceryListForPlan, generateGroceryListFromMeals]);

  const saveNewSectionOrder = async () => {
    try {
      if (!selectedStore) {
        // Fetch store if not already selected
        const storesResponse = await fetch('http://127.0.0.1:5000/api/stores');
        const storesData = await storesResponse.json();

        if (storesData.length === 0) {
          alert('No stores available to save section order');
          return;
        }

        const defaultStore = storesData.find(store => store.is_default) || storesData[0];
        setSelectedStore(defaultStore.id);

        // Pass the reordered section IDs
        const sectionIds = groceryList
          .filter(section => section.sectionId) // Only include sections with IDs
          .map(section => section.sectionId);
        await reorderSections(defaultStore.id, sectionIds);
      } else {
        const sectionIds = groceryList
          .filter(section => section.sectionId) // Only include sections with IDs
          .map(section => section.sectionId);
        await reorderSections(selectedStore, sectionIds);
      }

      setIsReordering(false);
      alert('Section order saved successfully!');
    } catch (error) {
      console.error('Error saving section order:', error);
      alert('Failed to save section order');
    }
  };

  // Function to make API call for reordering
  const reorderSections = async (storeId, sectionIds) => {
    if (!sectionIds || sectionIds.length === 0) {
      alert('No sections to reorder');
      return;
    }

    const response = await fetch(`http://127.0.0.1:5000/api/stores/${storeId}/sections/reorder`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sections: sectionIds
      })
    });

    if (!response.ok) {
      throw new Error('Failed to save section order');
    }
  };

  const printGroceryList = () => {
    setIsPrinting(true);
    setTimeout(() => {
      window.print();
      setIsPrinting(false);
    }, 100);
  };

  const exportGroceryListToCSV = () => {
    // Create CSV content
    let csvContent = "Section,Item,Quantity,Unit,Type\n";

    groceryList.forEach(section => {
      console.log("Processing section:", section.section);
      section.items.forEach(item => {
        // Clean up the item data and escape any commas
        const sectionName = section.section.replace(/,/g, " ");
        const itemName = item.name ? item.name.replace(/,/g, " ") : "";
        const quantity = item.formatted_combined || "";
        const unit = item.unit ? item.unit.replace(/,/g, " ") : "";
        const type = item.is_usda ? "USDA" : "Custom";

        csvContent += `${sectionName},${itemName},${quantity},${unit},${type}\n`;
      });
    });

    // Create a download link and trigger it
    const encodedUri = encodeURI("data:text/csv;charset=utf-8," + csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `grocery_list_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const savePlan = async () => {
    if (!planDetails?.isTemporary || !location.state || !location.state.meals) {
      return; // Only save if this is a temporary plan
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/api/weekly_plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: planDetails.name,
          meals: location.state.meals
        })
      });

      if (!response.ok) {
        throw new Error("Failed to save weekly plan");
      }

      const data = await response.json();

      // Update the plan details to reflect it's now saved
      setPlanDetails({
        ...planDetails,
        id: data.id,
        isTemporary: false
      });

      alert("Meal plan saved successfully!");

    } catch (err) {
      console.error("Error saving plan:", err);
      alert("Error saving plan: " + err.message);
    }
  };

  // Fixed handleCheckboxChange function to work with grouped items
  const handleCheckboxChange = (sectionIndex, groupKey) => {
    console.log(`Toggling checkbox for section ${sectionIndex}, group ${groupKey}`);

    setGroceryList(prevList => {
      const newList = JSON.parse(JSON.stringify(prevList)); // Deep copy
      const section = newList[sectionIndex];

      // Find all items in this section that match the groupKey
      const groupItems = section.items.filter(item =>
        (item.normalized_name || item.name.toLowerCase()) === groupKey
      );

      // Determine the new checked state (toggle based on current state)
      const currentCheckedState = groupItems.length > 0 && groupItems[0].checked;
      const newCheckedState = !currentCheckedState;

      // Update all matching items
      console.log("Processing section:", section.section);
      section.items.forEach(item => {
        if ((item.normalized_name || item.name.toLowerCase()) === groupKey) {
          item.checked = newCheckedState;
        }
      });

      return newList;
    });
  };

  // Go back to weekly planner
  const goToWeeklyPlanner = () => {
    navigate("/weekly-planner");
  };

  // Toggle USDA mode
  const toggleUsdaMode = () => {
    setUseUsda(prev => !prev);
  };

  // Render USDA badge for an ingredient
  const renderIngredientBadge = (item) => {
    if (item.is_usda) {
      return <span className="ingredient-badge usda-badge">USDA</span>;
    } else {
      return <span className="ingredient-badge custom-badge">Custom</span>;
    }
  };

  return (
    <div className={`grocery-list-container ${isPrinting ? 'printing' : ''} ${!detailedView ? 'hide-details' : ''}`}>
      <div className="grocery-list-header">
        <h1>Grocery List</h1>
        {planDetails && (
          <h2 className="plan-name">{planDetails.name}</h2>
        )}
      </div>

      <div className="grocery-list-actions no-print">
        <button className="back-btn" onClick={goToWeeklyPlanner}>
          ← Back to Planner
        </button>

        <div className="action-buttons">
          {planDetails && planDetails.isTemporary && (
            <button className="save-plan-btn" onClick={savePlan}>
              Save Meal Plan
            </button>
          )}

          <button
            className="organize-btn"
            onClick={() => navigate('/store-organizer')}>
            Organize Sections
          </button>

          {/* Add this new reorder button */}
          <button
            className={`reorder-btn ${isReordering ? 'active' : ''}`}
            onClick={() => setIsReordering(!isReordering)}>
            {isReordering ? 'Done Reordering' : 'Reorder Sections'}
          </button>

          <button className="print-btn" onClick={printGroceryList}>
            Print List
          </button>

          <button className="export-btn" onClick={exportGroceryListToCSV}>
            Export to CSV
          </button>

          <button
            className={`detail-toggle-btn ${detailedView ? 'active' : ''}`}
            onClick={() => setDetailedView(!detailedView)}
          >
            {detailedView ? 'Simple View' : 'Detailed View'}
          </button>

          {/* Add USDA toggle button */}
          <button
            className={`usda-toggle-btn ${useUsda ? 'active' : ''}`}
            onClick={toggleUsdaMode}
          >
            {useUsda ? 'USDA Enabled' : 'USDA Disabled'}
          </button>
        </div>
      </div>

      {/* USDA legend when enabled */}
      {useUsda && !isReordering && !isPrinting && (
        <div className="ingredient-legend no-print">
          <div className="legend-item">
            <span className="ingredient-badge usda-badge">USDA</span>
            <span>Standardized USDA ingredients</span>
          </div>
          <div className="legend-item">
            <span className="ingredient-badge custom-badge">Custom</span>
            <span>Custom user-created ingredients</span>
          </div>
        </div>
      )}

      {/* Show save button when reordering */}
      {isReordering && (
        <div className="reordering-actions no-print">
          <p>Drag sections to reorder them</p>
          <button className="save-order-btn" onClick={saveNewSectionOrder}>
            Save New Order
          </button>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading grocery list...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        isReordering ? (
          <div className="sections-container reordering">
            {groceryList.map((section, sectionIndex) => (
              section.items && section.items.length > 0 ? (
                <div key={section.section} className="grocery-section reorderable">
                  <h3 className="section-title">{section.section}</h3>
                  <div className="item-count">{section.items.length} items</div>
                  <div className="reorder-buttons">
                    <button
                      className="move-up-btn"
                      disabled={sectionIndex === 0}
                      onClick={() => {
                        const newList = [...groceryList];
                        [newList[sectionIndex], newList[sectionIndex - 1]] =
                          [newList[sectionIndex - 1], newList[sectionIndex]];
                        setGroceryList(newList);
                      }}
                    >
                      ↑
                    </button>
                    <button
                      className="move-down-btn"
                      disabled={sectionIndex === groceryList.length - 1}
                      onClick={() => {
                        const newList = [...groceryList];
                        [newList[sectionIndex], newList[sectionIndex + 1]] =
                          [newList[sectionIndex + 1], newList[sectionIndex]];
                        setGroceryList(newList);
                      }}
                    >
                      ↓
                    </button>
                  </div>
                </div>
              ) : null
            ))}
          </div>
        ) : (
          <div className="sections-container">
            {groceryList.map((section, sectionIndex) => (
              section.items && section.items.length > 0 ? (
                <div key={section.section} className="grocery-section">
                  <h3 className="section-title">{section.section}</h3>
                  <ul className="grocery-items">
                    {/* Group items by normalized name for display */}
                    {(() => {
                      // Group items by normalized name
                      const groupedItems = {};
                      console.log("Processing section:", section.section);

                      section.items.forEach(item => {
                        const key = item.normalized_name || item.name.toLowerCase();

                        if (!groupedItems[key]) {
                          // Initialize the group with the first item
                          groupedItems[key] = {
                            name: item.name,
                            normalized_name: key,
                            checked: item.checked || false,
                            quantities: item.quantities || [],
                            unit: item.unit || '',
                            combined_quantity: item.combined_quantity || 0,
                            formatted_combined: item.formatted_combined || '',
                            has_multiple_units: item.has_multiple_units || false,
                            is_usda: item.is_usda || false,
                            usda_fdc_id: item.usda_fdc_id || null,
                            // Make sure these fields are preserved
                            size: item.size || '',
                            descriptor: item.descriptor || '',
                            additional_descriptor: item.additional_descriptor || ''  // Keep original field name
                          };
                        } else {
                          // Update checked state (if any item is checked, the group is checked)
                          if (item.checked) {
                            groupedItems[key].checked = true;
                          }

                          // Update USDA status (if any item is USDA, the group is USDA)
                          if (item.is_usda) {
                            groupedItems[key].is_usda = true;
                            groupedItems[key].usda_fdc_id = item.usda_fdc_id;
                          }

                          // Ensure quantities array exists and is populated
                          if (item.quantities && item.quantities.length) {
                            if (!groupedItems[key].quantities) {
                              groupedItems[key].quantities = [];
                            }
                            // Only add quantities that aren't already in the group
                            item.quantities.forEach(qty => {
                              if (!groupedItems[key].quantities.some(
                                existingQty => existingQty.recipe_id === qty.recipe_id &&
                                  existingQty.quantity_text === qty.quantity_text)) {
                                groupedItems[key].quantities.push(qty);
                              }
                            });
                          }
                        }
                      });

                      // Render the grouped items
                      return Object.entries(groupedItems).map(([key, group], groupIndex) => (
                        <li
                          key={`${section.section}-${key}-${groupIndex}`}
                          className={`grocery-item ${group.checked ? 'checked' : ''}`}
                        >
                          <label className="checkbox-container">
                            <input
                              type="checkbox"
                              className="item-checkbox no-print"
                              checked={group.checked || false}
                              onChange={() => handleCheckboxChange(sectionIndex, key)}
                            />
                            <span className="checkmark no-print"></span>
                            <div className="item-details">
                              <span className="item-name">
                                {group.name || "Unnamed Item"}
                                {useUsda && renderIngredientBadge(group)}
                              </span>

                              {detailedView ? (
                                <div className="item-quantities">
                                  {group.quantities && group.quantities.length > 0 ? (
                                    group.quantities.map((qty, qIndex) => (
                                      <div key={qIndex} className="quantity-entry">
                                        {/* Base quantity and unit */}
                                        <span className="quantity-value">{qty.quantity_text}</span>

                                        {/* Additional descriptive fields - only show size and descriptor, not additional_descriptor */}
                                        {(group.size || group.descriptor) && (
                                          <span className="detailed-info">
                                            {group.size && <span className="item-size">{group.size}</span>}
                                            {group.descriptor && (
                                              <span className="item-descriptor">
                                                {group.size ? ', ' : ''}{group.descriptor}
                                              </span>
                                            )}
                                          </span>
                                        )}

                                        {/* Recipe source */}
                                        {qty.source && (
                                          <span className="quantity-source">from {qty.source}</span>
                                        )}
                                      </div>
                                    ))
                                  ) : (
                                    // Fallback display
                                    <span className="item-quantity">
                                      {group.formatted_combined ||
                                        (group.combined_quantity && group.unit ?
                                          `${group.combined_quantity} ${group.unit}` : "")}

                                      {/* Additional fields in fallback case - only size and descriptor */}
                                      {(group.size || group.descriptor) && (
                                        <span className="detailed-info">
                                          {group.size && <span className="item-size">{group.size}</span>}
                                          {group.descriptor && (
                                            <span className="item-descriptor">
                                              {group.size ? ', ' : ''}{group.descriptor}
                                            </span>
                                          )}
                                        </span>
                                      )}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                // Simple view remains unchanged
                                <span className="item-quantity">
                                  {group.formatted_combined || ""}
                                </span>
                              )}
                            </div>
                          </label>
                        </li>
                      ));
                    })()}
                  </ul>
                </div>
              ) : null
            ))}
          </div>
        )
      )}
    </div>
  );
}

export default GroceryListView;
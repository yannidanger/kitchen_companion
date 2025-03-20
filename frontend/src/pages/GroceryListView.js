import React, { useState, useEffect } from "react";
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
  }, [planId, location.state]);

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

  // Update the fetchGroceryListForPlan function
  const fetchGroceryListForPlan = async (id) => {
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

      // Then fetch grocery list
      const groceryResponse = await fetch(`http://127.0.0.1:5000/api/grocery_list?weekly_plan_id=${id}`);
      if (!groceryResponse.ok) {
        throw new Error("Failed to fetch grocery list");
      }

      const groceryData = await groceryResponse.json();

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
  };

  // Update the generateGroceryListFromMeals function similarly
  const generateGroceryListFromMeals = async (meals) => {
    try {
      setLoading(true);

      // Generate grocery list from meals array without saving the plan
      const response = await fetch(`http://127.0.0.1:5000/api/generate_grocery_list`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          meals: meals
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
    let csvContent = "Section,Item,Quantity,Unit\n";

    groceryList.forEach(section => {
      section.items.forEach(item => {
        // Clean up the item data and escape any commas
        const sectionName = section.section.replace(/,/g, " ");
        const itemName = item.name ? item.name.replace(/,/g, " ") : "";
        const quantity = item.quantity || "";
        const unit = item.unit ? item.unit.replace(/,/g, " ") : "";

        csvContent += `${sectionName},${itemName},${quantity},${unit}\n`;
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

  // In GroceryListView.js around line 116-125, modify the handleCheckboxChange function:
  const handleCheckboxChange = (sectionIndex, itemIndex) => {
    console.log(`Toggling checkbox for section ${sectionIndex}, item ${itemIndex}`);

    setGroceryList(prevList => {
      const newList = JSON.parse(JSON.stringify(prevList)); // Deep copy to ensure state changes
      newList[sectionIndex].items[itemIndex].checked =
        !newList[sectionIndex].items[itemIndex].checked;

      console.log(`New checked state: ${newList[sectionIndex].items[itemIndex].checked}`);
      return newList;
    });
  };

  // Go back to weekly planner
  const goToWeeklyPlanner = () => {
    navigate("/weekly-planner");
  };

  return (
    <div className={`grocery-list-container ${isPrinting ? 'printing' : ''}`}>
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
        </div>
      </div>

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
                    {section.items.map((item, itemIndex) => (
                      <li
                        key={`${section.section}-${itemIndex}`}
                        className={`grocery-item ${item.checked ? 'checked' : ''}`}
                      >
                        <label className="checkbox-container">
                          <input
                            type="checkbox"
                            className="item-checkbox no-print"
                            checked={item.checked || false}
                            onChange={() => handleCheckboxChange(sectionIndex, itemIndex)}
                          />
                          <span className="checkmark no-print"></span>
                          <div className="item-details">
                            <span className="item-name">
                              {item.name || item.main_text || ""}
                            </span>
                            <span className="item-quantity">
                              {item.formatted_quantity || item.fraction_str ||
                                (item.quantity !== undefined && item.unit ?
                                  `${item.quantity} ${item.unit}` :
                                  (item.precision_text || ""))}
                            </span>
                            {item.source && (
                              <span className="item-source">
                                from {item.source}
                              </span>
                            )}
                          </div>
                        </label>
                      </li>
                    ))}
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
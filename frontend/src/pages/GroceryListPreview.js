import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

function GroceryListPreview() {
  const location = useLocation();
  const navigate = useNavigate();

  const [groceryList, setGroceryList] = useState([]);
  const [planDetails, setPlanDetails] = useState({
    name: "Unnamed Meal Plan",
    isTemporary: true
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPrinting, setIsPrinting] = useState(false);

  useEffect(() => {
    if (location.state && location.state.meals) {
      // If we have meals data in location state, generate grocery list
      generateGroceryListFromMeals(location.state.meals);
      setPlanDetails({
        name: location.state.planName || "Unnamed Meal Plan",
        isTemporary: true
      });
    } else {
      // No meals data
      setError("No meal plan data found.");
      setLoading(false);
    }
  }, [location.state]);

  // In GroceryListPreview.js, update generateGroceryListFromMeals function
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
      setGroceryList(data.grocery_list || []);
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
        const itemName = item.main_text ? item.main_text.replace(/,/g, " ") : "";

        // Extract quantity and unit from precision_text if available
        let quantity = "";
        let unit = "";

        if (item.precision_text) {
          // Remove parentheses and split by space
          const parts = item.precision_text.replace(/[()]/g, "").split(" ");
          if (parts.length >= 1) {
            quantity = parts[0];
          }
          if (parts.length >= 2) {
            unit = parts.slice(1).join(" ");
          }
        }

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
    if (!location.state || !location.state.meals) {
      alert("No meal plan data to save.");
      return;
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
      alert("Meal plan saved successfully!");

      // Navigate to the saved plan's grocery list view
      navigate(`/grocery-list/${data.id}`);

    } catch (err) {
      console.error("Error saving plan:", err);
      alert("Error saving plan: " + err.message);
    }
  };

  const handlePlanNameChange = (e) => {
    setPlanDetails({
      ...planDetails,
      name: e.target.value
    });
  };

  const handleCheckboxChange = (sectionIndex, itemIndex) => {
    setGroceryList(prevList => {
      const newList = [...prevList];
      // Toggle the checked state if it exists, or set to true if it doesn't
      newList[sectionIndex].items[itemIndex].checked =
        !newList[sectionIndex].items[itemIndex].checked;
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
        <h1>Grocery List Preview</h1>
        <div className="plan-name-edit no-print">
          <input
            type="text"
            value={planDetails.name}
            onChange={handlePlanNameChange}
            placeholder="Enter a name for your meal plan"
          />
        </div>
        <h2 className="plan-name print-only">{planDetails.name}</h2>
      </div>

      <div className="grocery-list-actions no-print">
        <button className="back-btn" onClick={goToWeeklyPlanner}>
          ← Back to Planner
        </button>

        <div className="action-buttons">
          <button className="save-plan-btn" onClick={savePlan}>
            Save Meal Plan
          </button>

          <button className="print-btn" onClick={printGroceryList}>
            Print List
          </button>

          <button className="export-btn" onClick={exportGroceryListToCSV}>
            Export to CSV
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">Generating grocery list...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <div className="grocery-list-content">
          {groceryList.length === 0 ? (
            <div className="empty-list">
              <p>No items found in your grocery list.</p>
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
                              {/* Add this console.log to debug what properties are available */}
                              {console.log('Item data:', item)}

                              <span className="item-name">
                                {/* Try all possible properties that might contain the name */}
                                {item.name || item.main_text || item.item_name ||
                                  (typeof item === 'string' ? item : "Unnamed Item")}
                              </span>

                              <span className="item-quantity">
                                {item.formatted_quantity || item.fraction_str ||
                                  (item.quantity !== undefined ?
                                    (item.unit ? `${item.quantity} ${item.unit}` : item.quantity) :
                                    (item.precision_text || ""))}
                              </span>
                            </div>
                          </label>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default GroceryListPreview;
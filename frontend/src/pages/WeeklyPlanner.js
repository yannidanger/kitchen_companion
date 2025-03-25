import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";

function WeeklyPlanner() {
  const navigate = useNavigate();
  const [recipes, setRecipes] = useState([]);
  const [weeklyPlan, setWeeklyPlan] = useState({
    name: `Meal Plan for Week of ${new Date().toLocaleDateString()}`,
    meals: []
  });
  const [availablePlans, setAvailablePlans] = useState([]);
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [savedSuccessfully, setSavedSuccessfully] = useState(false);

  const days = useMemo(() => [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
  ], []);

  // Available meal types
  const defaultMealTypes = useMemo(() => ["Breakfast", "Lunch", "Dinner"], []);

  // Custom meal slots state
  const [customMealSlots, setCustomMealSlots] = useState({});
  const [newCustomSlot, setNewCustomSlot] = useState({
    day: days[0],
    name: "",
    person: ""
  });

  // Fetch all recipes
  useEffect(() => {
    fetchRecipes();
    fetchSavedPlans();
  }, [customMealSlots, days, defaultMealTypes]);

  const fetchRecipes = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/recipes");
      const data = await response.json();
      setRecipes(data);
    } catch (error) {
      console.error("Error fetching recipes:", error);
    }
  };

  const fetchSavedPlans = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/weekly_plan_list");
      const data = await response.json();
      setAvailablePlans(data);
    } catch (error) {
      console.error("Error fetching saved plans:", error);
    }
  };

  const fetchPlanDetails = async (planId) => {
    if (!planId) return;

    try {
      const response = await fetch(`http://127.0.0.1:5000/api/weekly_plan/${planId}`);
      const data = await response.json();

      // Transform the data to our expected format
      const transformedPlan = {
        name: data.name,
        meals: data.meals.map(meal => ({
          day: meal.day,
          meal_type: meal.meal_type,
          recipe_id: meal.recipe_id
        }))
      };

      setWeeklyPlan(transformedPlan);

      // Populate custom meal slots from existing data
      const customSlots = {};
      data.meals.forEach(meal => {
        // If this isn't a default meal type, add it to custom slots
        if (!defaultMealTypes.includes(meal.meal_type.split(" (")[0])) {
          const [mealName, person] = meal.meal_type.includes(" (") ?
            [meal.meal_type.split(" (")[0], meal.meal_type.split(" (")[1].replace(")", "")] :
            [meal.meal_type, ""];

          if (!customSlots[meal.day]) {
            customSlots[meal.day] = [];
          }

          customSlots[meal.day].push({
            name: mealName,
            person: person
          });
        }
      });

      setCustomMealSlots(customSlots);
    } catch (error) {
      console.error("Error fetching plan details:", error);
    }
  };

  // Initialize meal slots for each day and default meal types
  // Initialize meal slots for each day and default meal types
  useEffect(() => {
    const initialMeals = [];

    days.forEach(day => {
      defaultMealTypes.forEach(mealType => {
        initialMeals.push({
          day: day,
          meal_type: mealType,
          recipe_id: ""
        });
      });

      // Add custom meal slots if any
      if (customMealSlots[day]) {
        customMealSlots[day].forEach(slot => {
          const mealType = slot.person ?
            `${slot.name} (${slot.person})` :
            slot.name;

          initialMeals.push({
            day: day,
            meal_type: mealType,
            recipe_id: ""
          });
        });
      }
    });

    setWeeklyPlan(prev => ({
      ...prev,
      meals: initialMeals
    }));
  }, [customMealSlots, days, defaultMealTypes]);

  // Handle recipe selection for a meal slot
  const handleRecipeSelect = (day, mealType, recipeId) => {
    setWeeklyPlan(prev => ({
      ...prev,
      meals: prev.meals.map(meal => {
        if (meal.day === day && meal.meal_type === mealType) {
          return { ...meal, recipe_id: recipeId };
        }
        return meal;
      })
    }));
  };

  // Add a custom meal slot
  const addCustomMealSlot = () => {
    if (!newCustomSlot.name.trim()) {
      alert("Please enter a name for the custom meal slot");
      return;
    }

    const day = newCustomSlot.day;
    const newSlot = {
      name: newCustomSlot.name,
      person: newCustomSlot.person
    };

    setCustomMealSlots(prev => {
      const updatedSlots = { ...prev };
      if (!updatedSlots[day]) {
        updatedSlots[day] = [];
      }
      updatedSlots[day] = [...updatedSlots[day], newSlot];
      return updatedSlots;
    });

    // Reset the form
    setNewCustomSlot({
      day: days[0],
      name: "",
      person: ""
    });
  };

  // Remove a custom meal slot
  const removeCustomMealSlot = (day, index) => {
    setCustomMealSlots(prev => {
      const updatedSlots = { ...prev };
      updatedSlots[day] = updatedSlots[day].filter((_, i) => i !== index);

      // If there are no more slots for this day, remove the day entry
      if (updatedSlots[day].length === 0) {
        delete updatedSlots[day];
      }

      return updatedSlots;
    });

    // Also remove from the weekly plan if it exists
    setWeeklyPlan(prev => {
      const mealType = prev.meals.find(meal =>
        meal.day === day &&
        meal.meal_type === `${customMealSlots[day][index].name} (${customMealSlots[day][index].person})`
      )?.meal_type;

      if (mealType) {
        return {
          ...prev,
          meals: prev.meals.filter(meal => !(meal.day === day && meal.meal_type === mealType))
        };
      }

      return prev;
    });
  };

  // Save the weekly plan
  const saveWeeklyPlan = async () => {
    try {
      // Filter out meals with no recipe selected
      const filledMeals = weeklyPlan.meals.filter(meal => meal.recipe_id);

      if (filledMeals.length === 0) {
        alert("Please select at least one recipe for your meal plan");
        return;
      }

      const response = await fetch("http://127.0.0.1:5000/api/weekly_plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: weeklyPlan.name,
          meals: filledMeals
        })
      });

      if (!response.ok) {
        throw new Error("Failed to save weekly plan");
      }

      await response.json();
      setSavedSuccessfully(true);

      // Refresh the available plans list
      fetchSavedPlans();

      // Set a timeout to hide the success message after 3 seconds
      setTimeout(() => {
        setSavedSuccessfully(false);
      }, 3000);

    } catch (error) {
      console.error("Error saving weekly plan:", error);
      alert("Error saving weekly plan: " + error.message);
    }
  };

  // Generate grocery list without saving the plan
  const generateGroceryList = async () => {
    try {
      // Filter out meals with no recipe selected
      const filledMeals = weeklyPlan.meals.filter(meal => meal.recipe_id);

      if (filledMeals.length === 0) {
        alert("Please select at least one recipe for your meal plan");
        return;
      }

      // Navigate to grocery list page with plan data
      // We'll need to create a new route and component for this
      navigate("/grocery-list-preview", {
        state: {
          meals: filledMeals,
          planName: weeklyPlan.name
        }
      });

    } catch (error) {
      console.error("Error generating grocery list:", error);
      alert("Error generating grocery list: " + error.message);
    }
  };

  // Handle plan name change
  const handlePlanNameChange = (e) => {
    setWeeklyPlan(prev => ({
      ...prev,
      name: e.target.value
    }));
  };

  // Handle selecting a saved plan
  const handleSelectPlan = (e) => {
    const planId = e.target.value;
    setSelectedPlanId(planId);

    if (planId) {
      fetchPlanDetails(planId);
    } else {
      // Reset to default if "Create New" is selected
      setWeeklyPlan({
        name: `Meal Plan for Week of ${new Date().toLocaleDateString()}`,
        meals: []
      });
      setCustomMealSlots({});
    }
  };

  // Get recipe name by ID
  const getRecipeName = (recipeId) => {
    const recipe = recipes.find(r => r.id === parseInt(recipeId));
    return recipe ? recipe.name : "";
  };

  return (
    <div className="weekly-planner-container">
      <div className="weekly-planner-header">
        <h1>Weekly Meal Planner</h1>
        {savedSuccessfully && (
          <div className="success-message">
            Plan saved successfully!
          </div>
        )}
      </div>

      <div className="plan-controls">
        {/* Load saved plan dropdown */}
        <div className="plan-selector">
          <label htmlFor="saved-plans">Load Saved Plan:</label>
          <select
            id="saved-plans"
            value={selectedPlanId}
            onChange={handleSelectPlan}
          >
            <option value="">Create New</option>
            {availablePlans.map(plan => (
              <option key={plan.id} value={plan.id}>
                {plan.name}
              </option>
            ))}
          </select>
        </div>

        {/* Plan name input */}
        <div className="plan-name-container">
          <label htmlFor="plan-name">Plan Name:</label>
          <input
            id="plan-name"
            type="text"
            value={weeklyPlan.name}
            onChange={handlePlanNameChange}
            placeholder="Enter a name for your meal plan"
          />
        </div>

        {/* Save and generate grocery list buttons */}
        <div className="plan-actions">
          <button
            className="save-plan-btn"
            onClick={saveWeeklyPlan}
          >
            Save Plan
          </button>
          <button
            className="organize-ingredients-btn"
            onClick={() => navigate(`/store-organizer?weekly_plan_id=${selectedPlanId}`)}
            disabled={!selectedPlanId}
          >
            Organize Ingredients for This Meal Plan
          </button>
          <button
            className="generate-list-btn"
            onClick={generateGroceryList}
          >
            Generate Grocery List
          </button>
        </div>
      </div>

      {/* Custom meal slot creator */}
      <div className="custom-meal-creator">
        <h3>Add Custom Meal Slot</h3>
        <div className="custom-meal-form">
          <div className="form-group">
            <label htmlFor="custom-day">Day:</label>
            <select
              id="custom-day"
              value={newCustomSlot.day}
              onChange={(e) => setNewCustomSlot({ ...newCustomSlot, day: e.target.value })}
            >
              {days.map(day => (
                <option key={day} value={day}>{day}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="custom-name">Meal Name:</label>
            <input
              id="custom-name"
              type="text"
              value={newCustomSlot.name}
              onChange={(e) => setNewCustomSlot({ ...newCustomSlot, name: e.target.value })}
              placeholder="e.g., Snack, Dessert"
            />
          </div>

          <div className="form-group">
            <label htmlFor="custom-person">Person (Optional):</label>
            <input
              id="custom-person"
              type="text"
              value={newCustomSlot.person}
              onChange={(e) => setNewCustomSlot({ ...newCustomSlot, person: e.target.value })}
              placeholder="e.g., Johnny, Suzy"
            />
          </div>

          <button
            className="add-custom-btn"
            onClick={addCustomMealSlot}
          >
            Add Meal Slot
          </button>
        </div>
      </div>

      {/* Weekly meal planner grid */}
      <div className="meal-planner-grid">
        <div className="day-headers">
          <div className="meal-type-header"></div> {/* Empty cell for alignment */}
          {days.map(day => (
            <div key={day} className="day-header">
              {day}
            </div>
          ))}
        </div>

        {/* Default meal types */}
        {defaultMealTypes.map(mealType => (
          <div className="meal-row" key={mealType}>
            <div className="meal-type-label">{mealType}</div>
            {days.map(day => {
              const meal = weeklyPlan.meals.find(
                m => m.day === day && m.meal_type === mealType
              );
              const recipeId = meal ? meal.recipe_id : "";

              return (
                <div key={`${day}-${mealType}`} className="meal-cell">
                  <select
                    value={recipeId}
                    onChange={(e) => handleRecipeSelect(day, mealType, e.target.value)}
                  >
                    <option value="">Select a recipe...</option>
                    {recipes.map(recipe => (
                      <option key={recipe.id} value={recipe.id}>
                        {recipe.name}
                      </option>
                    ))}
                  </select>
                  {recipeId && (
                    <div className="selected-recipe-name">
                      {getRecipeName(recipeId)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}

        {/* Custom meal slots for each day */}
        {Object.entries(customMealSlots).map(([day, slots]) =>
          slots.map((slot, index) => {
            const mealType = slot.person ? `${slot.name} (${slot.person})` : slot.name;
            const meal = weeklyPlan.meals.find(
              m => m.day === day && m.meal_type === mealType
            );
            const recipeId = meal ? meal.recipe_id : "";

            return (
              <div
                className="custom-meal-row"
                key={`${day}-${mealType}-${index}`}
              >
                <div className="meal-type-label custom-meal">
                  <span>{mealType}</span>
                  <button
                    className="remove-slot-btn"
                    onClick={() => removeCustomMealSlot(day, index)}
                  >
                    ✕
                  </button>
                </div>

                {days.map(gridDay => (
                  <div
                    key={`${gridDay}-${mealType}`}
                    className={`meal-cell ${gridDay === day ? 'active' : 'inactive'}`}
                  >
                    {gridDay === day ? (
                      <>
                        <select
                          value={recipeId}
                          onChange={(e) => handleRecipeSelect(day, mealType, e.target.value)}
                        >
                          <option value="">Select a recipe...</option>
                          {recipes.map(recipe => (
                            <option key={recipe.id} value={recipe.id}>
                              {recipe.name}
                            </option>
                          ))}
                        </select>
                        {recipeId && (
                          <div className="selected-recipe-name">
                            {getRecipeName(recipeId)}
                          </div>
                        )}
                      </>
                    ) : null}
                  </div>
                ))}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default WeeklyPlanner;
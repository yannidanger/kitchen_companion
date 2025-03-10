import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function SavedGroceryLists() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWeeklyPlans();
  }, []);

  const fetchWeeklyPlans = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://127.0.0.1:5000/api/weekly_plan_list");
      
      if (!response.ok) {
        throw new Error("Failed to fetch weekly plans");
      }
      
      const data = await response.json();
      
      // Get more details for each plan
      const plansWithDetails = await Promise.all(
        data.map(async (plan) => {
          try {
            const detailsResponse = await fetch(`http://127.0.0.1:5000/api/weekly_plan/${plan.id}`);
            if (detailsResponse.ok) {
              const detailsData = await detailsResponse.json();
              return {
                ...plan,
                meals: detailsData.meals || [],
                ingredients: detailsData.ingredient_count || 0,
                created_at: detailsData.created_at || null
              };
            }
            return plan;
          } catch (err) {
            console.error(`Error fetching details for plan ${plan.id}:`, err);
            return plan;
          }
        })
      );
      
      setPlans(plansWithDetails);
      setLoading(false);
      
    } catch (err) {
      console.error("Error fetching weekly plans:", err);
      setError(err.message);
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "Unknown date";
    
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const handleViewGroceryList = (planId) => {
    navigate(`/grocery-list/${planId}`);
  };

  const handleDeletePlan = async (planId) => {
    if (!window.confirm("Are you sure you want to delete this meal plan?")) {
      return;
    }
    
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/weekly_plan/${planId}`, {
        method: "DELETE",
      });
      
      if (!response.ok) {
        throw new Error("Failed to delete meal plan");
      }
      
      // Refresh the list after deletion
      fetchWeeklyPlans();
      
    } catch (err) {
      console.error("Error deleting meal plan:", err);
      alert("Error deleting meal plan: " + err.message);
    }
  };

  return (
    <div className="saved-lists-container">
      <div className="saved-lists-header">
        <h1>Saved Grocery Lists</h1>
      </div>
      
      {loading ? (
        <div className="loading">Loading saved grocery lists...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : (
        <>
          {plans.length === 0 ? (
            <div className="empty-state">
              <h3>No saved grocery lists found</h3>
              <p>Create a weekly meal plan to generate a grocery list.</p>
              <button 
                className="create-plan-btn"
                onClick={() => navigate("/weekly-planner")}
              >
                Create Meal Plan
              </button>
            </div>
          ) : (
            <div className="plans-list">
              {plans.map((plan) => (
                <div key={plan.id} className="plan-card">
                  <div className="plan-info">
                    <h3 className="plan-name">{plan.name}</h3>
                    <div className="plan-meta">
                      <span className="plan-date">
                        Created: {formatDate(plan.created_at)}
                      </span>
                      <span className="plan-stats">
                        {plan.meals?.length || 0} meals, {plan.ingredients || 0} ingredients
                      </span>
                    </div>
                  </div>
                  <div className="plan-actions">
                    <button 
                      className="view-list-btn"
                      onClick={() => handleViewGroceryList(plan.id)}
                    >
                      View Grocery List
                    </button>
                    <button 
                      className="edit-plan-btn"
                      onClick={() => navigate(`/weekly-planner?planId=${plan.id}`)}
                    >
                      Edit Plan
                    </button>
                    <button 
                      className="delete-plan-btn"
                      onClick={() => handleDeletePlan(plan.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default SavedGroceryLists;
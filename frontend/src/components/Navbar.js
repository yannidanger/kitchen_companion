import React from "react";
import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="app-title">Kitchen Companion</div>
      
      <div className="nav-links">
        <Link to="/" className="nav-link">Home</Link>
        
        {/* Recipes Dropdown */}
        <div className="dropdown">
          <button className="dropbtn">Recipes ▼</button>
          <div className="dropdown-content">
            <Link to="/recipes">➕ Add a Recipe</Link>
            <Link to="/recipe-management">📋 View, Edit, or Delete</Link>
          </div>
        </div>
        
        {/* Weekly Planner */}
        <Link to="/weekly-planner" className="nav-link">Weekly Planner</Link>
        
        {/* Grocery Lists Dropdown */}
        <div className="dropdown">
          <button className="dropbtn">Grocery Lists ▼</button>
          <div className="dropdown-content">
            <Link to="/weekly-planner">🗓️ Create from Meal Plan</Link>
            <Link to="/saved-grocery-lists">📝 View Saved Lists</Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
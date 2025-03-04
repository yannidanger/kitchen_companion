import React from "react";
import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav style={{ padding: "10px", borderBottom: "2px solid #ccc" }}>
      <Link to="/" style={{ marginRight: "15px" }}>Home</Link>
      
      {/* Recipes Dropdown */}
      <div className="dropdown">
        <button className="dropbtn">Recipes ▼</button>
        <div className="dropdown-content">
          <Link to="/recipes">➕ Add a Recipe</Link>
          <Link to="/recipe-management">📋 View, Edit, or Delete</Link>
        </div>
      </div>

      <Link to="/grocery-list">Grocery List</Link>
    </nav>
  );
}

export default Navbar;

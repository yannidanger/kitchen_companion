import React from "react";
import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav style={{ padding: "10px", borderBottom: "2px solid #ccc" }}>
      <Link to="/" style={{ marginRight: "15px" }}>Home</Link>
      <Link to="/recipes" style={{ marginRight: "15px" }}>Recipes</Link>
      <Link to="/grocery-list">Grocery List</Link>
    </nav>
  );
}

export default Navbar;

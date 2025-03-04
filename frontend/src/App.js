import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Recipes from "./pages/Recipes";
import GroceryList from "./pages/GroceryList";
import Navbar from "./components/Navbar";
import RecipeManagement from "./pages/RecipeManagement"; 
import RecipeDetail from "./pages/RecipeDetail";


function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/recipes" element={<Recipes />} />
        <Route path="/recipe-management" element={<RecipeManagement />} />
        <Route path="/recipes/:recipeId/edit" element={<RecipeDetail />} />
        <Route path="/grocery-list" element={<GroceryList />} />
      </Routes>
    </Router>
  );
}

export default App;

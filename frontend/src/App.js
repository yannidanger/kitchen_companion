import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Recipes from "./pages/Recipes";
import RecipeDetail from "./pages/RecipeDetail";
import RecipeManagement from "./pages/RecipeManagement";
import WeeklyPlanner from "./pages/WeeklyPlanner";
import GroceryListView from "./pages/GroceryListView";
import GroceryListPreview from "./pages/GroceryListPreview";
import SavedGroceryLists from "./pages/SavedGroceryLists";
import StoreOrganizer from './components/StoreOrganizerFixed';
import "./styles/main.css";

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <div className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/recipes" element={<Recipes />} />
            <Route path="/recipes/:recipeId/edit" element={<RecipeDetail />} />
            <Route path="/recipe-management" element={<RecipeManagement />} />
            <Route path="/weekly-planner" element={<WeeklyPlanner />} />
            <Route path="/grocery-list/:planId" element={<GroceryListView />} />
            <Route path="/grocery-list-preview" element={<GroceryListPreview />} />
            <Route path="/saved-grocery-lists" element={<SavedGroceryLists />} />
            <Route path="/store-organizer" element={<StoreOrganizer />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
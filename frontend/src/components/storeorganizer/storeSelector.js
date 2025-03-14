import React, { useState } from "react";

const StoreSelector = ({ stores, selectedStore, onChange, onCreateStore }) => {
    const [isCreating, setIsCreating] = useState(false);
    const [newStoreName, setNewStoreName] = useState("");
    
    // Remove these unused variables:
    // const [isEditing, setIsEditing] = useState(false);
    // const [editName, setEditName] = useState("");

    const handleCreateStore = () => {
        if (!newStoreName.trim()) return;
        
        onCreateStore(newStoreName);
        setNewStoreName("");
        setIsCreating(false);
    };

    return (
        <div className="store-selector">
            <div className="store-selector-controls">
                <label htmlFor="store-select">Store Profile:</label>
                <select 
                    id="store-select"
                    value={selectedStore || ""}
                    onChange={(e) => onChange(e.target.value)}
                >
                    {stores.map(store => (
                        <option key={store.id} value={store.id}>
                            {store.name} {store.is_default ? "(Default)" : ""}
                        </option>
                    ))}
                </select>
                
                <button 
                    className="store-action-btn"
                    onClick={() => setIsCreating(!isCreating)}
                >
                    {isCreating ? "Cancel" : "New Store"}
                </button>
            </div>

            {isCreating && (
                <div className="store-form">
                    <input
                        type="text"
                        placeholder="New Store Name"
                        value={newStoreName}
                        onChange={(e) => setNewStoreName(e.target.value)}
                    />
                    <button 
                        className="store-form-btn"
                        onClick={handleCreateStore}
                        disabled={!newStoreName.trim()}
                    >
                        Create Store
                    </button>
                </div>
            )}
        </div>
    );
};

export default StoreSelector;
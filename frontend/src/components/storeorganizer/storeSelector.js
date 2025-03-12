import React from "react";

const StoreSelector = ({ stores, selectedStore, onChange }) => {
    return (
        <div className="store-selector">
            <label htmlFor="store-select">Select Store:</label>
            <select 
                id="store-select"
                value={selectedStore || ""}
                onChange={(e) => onChange(e.target.value)}
            >
                {stores.map(store => (
                    <option key={store.id} value={store.id}>{store.name}</option>
                ))}
            </select>
        </div>
    );
};

export default StoreSelector;
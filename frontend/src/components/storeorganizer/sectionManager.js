import React from "react";

const SectionManager = ({ newSectionName, setNewSectionName, addNewSection }) => {
    const handleSubmit = () => {
        if (!newSectionName.trim()) {
            return; // Don't submit empty names
        }
        addNewSection(newSectionName);
        setNewSectionName("");
    };

    return (
        <div className="add-section-form">
            <input
                type="text"
                value={newSectionName}
                onChange={(e) => setNewSectionName(e.target.value)}
                placeholder="New Section Name"
            />
            <button onClick={handleSubmit}>Add Section</button>
        </div>
    );
};

export default SectionManager;
import React from "react";

const SectionManager = ({ newSectionName, setNewSectionName, addNewSection }) => {
    const handleSubmit = () => {
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
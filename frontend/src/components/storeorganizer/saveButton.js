import React from "react";

const SaveButton = ({ onClick }) => {
    return (
        <button className="save-organization-btn" onClick={onClick}>
            Save Organization
        </button>
    );
};

export default SaveButton;
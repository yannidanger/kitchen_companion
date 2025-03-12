import React from "react";

const DebugButton = ({ onClick }) => {
    return (
        <button onClick={onClick} style={{ marginLeft: '10px' }}>
            Debug Move
        </button>
    );
};

export default DebugButton;
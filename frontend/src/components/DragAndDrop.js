import React from 'react';
import './DragAndDrop.css'; // Import the CSS file

const DragAndDrop = () => {
  return (
    <div className="d-flex align-items-center justify-content-center">
      <div className="card p-5" data-bs-theme="dark" id="dragAndDrop">
        <div className="card-body border">
          <div className="center-content">
            <i className="fas fa-cloud cloud-icon"></i>
            <p className="card-text">Drag and drop your report here</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DragAndDrop;

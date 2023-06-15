import React from "react";
import "./DragAndDrop.css";
import { CloudArrowUpFill } from "react-bootstrap-icons";

const DragAndDrop = () => {
  return (
    <div className="center-content">
      <div className="card" data-bs-theme="dark" id="dragAndDrop">
        <div className="card-body d-flex flex-column align-items-center justify-content-center">
          <CloudArrowUpFill size={80} />
          <h5 className="card-text">Drag your local report here!</h5>
        </div>
      </div>
    </div>
  );
};

export default DragAndDrop;

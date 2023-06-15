import { useState, useRef, useEffect } from "react";
import { useSpring, animated } from "react-spring";
import "./DragAndDrop.css";
import { CloudArrowUpFill } from "react-bootstrap-icons";

function DragAndDrop() {
  const [dragActive, setDragActive] = useState(false);
  const [fileUploaded, setFileUploaded] = useState(false);
  const inputRef = useRef(null);

  const flyingAnimation = useSpring({
    transform: fileUploaded ? "translateY(-100%)" : "translateY(0%)",
  });

  const handleDrag = function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = function (e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
      setFileUploaded(true);
      setTimeout(() => {
        setFileUploaded(false);
      }, 1000);
      console.log(e.dataTransfer.files[0]);
    }
  };

  const handleChange = function (e) {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
      setFileUploaded(true);
      setTimeout(() => {
        setFileUploaded(false);
      }, 1000);
      console.log(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    inputRef.current.click();
  };

  const handleFiles = (file) => {};

  return (
    <div className="card-body d-grid justify-content-center mt-5">
      <form
        id="form-file-upload"
        onDragEnter={handleDrag}
        onSubmit={(e) => e.preventDefault()}
      >
        <input
          ref={inputRef}
          type="file"
          id="input-file-upload"
          className="d-none"
          accept=".json,.jsonl"
          multiple={false}
          onChange={handleChange}
        />

        <label
          id="label-file-upload"
          htmlFor="input-file-upload"
          className={dragActive ? "drag-active" : ""}
        >
          <div className="text-center">
            <animated.div style={flyingAnimation}>
              <CloudArrowUpFill size={80} />
            </animated.div>
            <p className="card-text">Drag your local report here!</p>
            <button className="btn btn-primary" onClick={onButtonClick}>
              Upload report
            </button>
          </div>
        </label>
        {dragActive && (
          <div
            id="drag-file-element"
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          ></div>
        )}
      </form>
    </div>
  );
}

export default DragAndDrop;

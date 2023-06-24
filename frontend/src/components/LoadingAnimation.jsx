const LoadingAnimation = () => {
  const spinnerStyle = {
    width: "8rem",
    height: "8rem",
  };
  return (
    <>
      <div className="d-grid justify-content-center ">
        <div
          className="d-flex justify-content-center align-items-center"
          style={{ height: "50vh" }}
        >
          <div className="spinner-border" style={spinnerStyle} role="status">
            <span className="sr-only"></span>
          </div>
        </div>
        <h4>Loading... Please wait!</h4>
      </div>
    </>
  );
};

export default LoadingAnimation;

import Spinner from "react-bootstrap/Spinner";

const LoadingAnimation = () => {
  const spinnerStyle = {
    width: "8rem",
    height: "8rem",
  };
  return (
    <div
      className="d-flex justify-content-center align-items-center"
      style={{ height: "50vh" }}
    >
      <Spinner
        animation="border"
        variant="info"
        style={spinnerStyle}
        role="status"
      />
    </div>
  );
};

export default LoadingAnimation;

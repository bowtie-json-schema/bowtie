import {
  CheckCircleFill,
  ExclamationOctagon,
  XCircleFill,
} from "react-bootstrap-icons";

const AccordionSvg = ({ testResult }) => {
  let svgComponent;

  switch (testResult) {
    case "skipped":
      svgComponent = <ExclamationOctagon />;
      break;
    case "errored":
      svgComponent = <ExclamationOctagon />;
      break;
    case "successful":
      svgComponent = <CheckCircleFill />;
      break;
    case "unexpectedlyValid":
      svgComponent = <CheckCircleFill />;
      break;
    case "unexpectedlyInvalid":
      svgComponent = <XCircleFill />;
      break;
    default:
      return null;
  }

  return (
    <td
      className={`text-center ${
        testResult === "skipped" || testResult === "errored"
          ? "text-bg-warning"
          : testResult === "unexpectedlyValid" ||
            testResult === "unexpectedlyInvalid"
          ? "text-bg-danger"
          : ""
      }`}
    >
      {svgComponent}
    </td>
  );
};

export default AccordionSvg;

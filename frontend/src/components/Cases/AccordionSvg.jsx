import {
  CheckCircleFill,
  ExclamationOctagon,
  XCircleFill,
} from "react-bootstrap-icons";

const AccordionSvg = ({ result }) => {
  if (result.state === "skipped" || result.state === "errored") {
    return (
      <td className="text-center text-bg-warning">
        <ExclamationOctagon />
      </td>
    );
  } else {
    const borderClass = result.state === "successful" ? "" : "text-bg-danger";
    const svgComponent = result.valid ? <CheckCircleFill /> : <XCircleFill />;
    return <td className={`text-center ${borderClass}`}>{svgComponent}</td>;
  }
};

export default AccordionSvg;

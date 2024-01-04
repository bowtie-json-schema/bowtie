import {
  CheckCircleFill,
  ExclamationOctagon,
  XCircleFill,
} from "react-bootstrap-icons";
import { CaseResult } from "../../data/parseReportData";

interface CaseResultProps {
  result: CaseResult;
}

const stateToTile = {
  successful: "Correct result",
  failed: "Incorrect result",
  skipped: "Case skipped",
  errored: "Case errored",
};

const CaseResultSvg = ({ result }: CaseResultProps) => {
  if (result.state === "skipped" || result.state === "errored") {
    const borderClass =
      result.state === "skipped" ? "text-bg-warning" : "text-bg-danger";
    return (
      <td
        className={`text-center align-middle ${borderClass}`}
        title={stateToTile[result.state]}
      >
        <ExclamationOctagon />
      </td>
    );
  } else {
    const borderClass = result.state === "successful" ? "" : "text-bg-danger";
    const svgComponent = result.valid ? <CheckCircleFill /> : <XCircleFill />;
    return (
      <td
        className={`text-center align-middle ${borderClass}`}
        title={stateToTile[result.state]}
      >
        {svgComponent}
      </td>
    );
  }
};

export default CaseResultSvg;

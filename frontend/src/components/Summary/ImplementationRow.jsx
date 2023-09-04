import "./ImplementationRow.css";
import { InfoCircleFill } from "react-bootstrap-icons";
import { useState } from "react";
import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { RunTimeInfoModal } from "../Modals/RunTimeInfoModal";
import { mapLanguage } from "../../data/mapLanguage";

const ImplementationRow = ({ cases, implementation }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showRunTimeInfo, setShowRunTimeInfo] = useState(false);

  return (
    <tr>
      <th scope="row">
        <a
          href={
            implementation.metadata.homepage ?? implementation.metadata.issues
          }
        >
          {implementation.metadata.name}
        </a>
        <small className="text-muted ps-1">
          {mapLanguage(implementation.metadata.language)}
        </small>
      </th>
      <td>
        <small className="font-monospace text-muted">
          {implementation.metadata.version ?? ""}
        </small>
        <button
          className="btn border-0"
          onClick={() => setShowRunTimeInfo(true)}
        >
          <InfoCircleFill />
        </button>
      </td>

      <td className="text-center">{implementation.erroredCases}</td>
      <td className="text-center">{implementation.skippedTests}</td>
      <td className="text-center details-required">
        {implementation.failedTests + implementation.erroredTests}
        <div className="hover-details text-center">
          <p>
            <b>failed</b>:{implementation.failedTests}
          </p>
          <p>
            <b>errored</b>:{implementation.erroredTests}
          </p>
        </div>
      </td>

      <td>
        <button
          type="button"
          className="btn btn-sm btn-primary"
          onClick={() => setShowDetails(true)}
        >
          Details
        </button>
      </td>
      <RunTimeInfoModal
        show={showRunTimeInfo}
        handleClose={() => setShowRunTimeInfo(false)}
        implementation={implementation}
      />
      <DetailsButtonModal
        show={showDetails}
        handleClose={() => setShowDetails(false)}
        cases={cases}
        implementation={implementation}
      />
    </tr>
  );
};

export default ImplementationRow;

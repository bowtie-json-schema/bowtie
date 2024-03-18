import "./ImplementationRow.css";
import { useState } from "react";
import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { mapLanguage } from "../../data/mapLanguage";
import { useNavigate } from "react-router-dom";
import {
  Case,
  Implementation,
  ImplementationResults,
} from "../../data/parseReportData";

const ImplementationRow = ({
  cases,
  implementationResults,
  implementation,
}: {
  cases: Map<number, Case>;
  implementationResults: ImplementationResults;
  implementation: Implementation;
  key: number;
  index: number;
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const navigate = useNavigate();
  const implementationPath = getImplementationPath(implementationResults);

  return (
    <tr>
      <th
        className="table-implementation-name align-middle p-0"
        onClick={() => navigate(`/implementations/${implementationPath}`)}
        scope="row"
      >
        <span className="text-decoration-underline text-primary">
          {implementation.name}
        </span>
        <small className="text-muted ps-1">
          {mapLanguage(implementation.language)}
        </small>
      </th>
      <td className="align-middle d-none d-sm-table-cell">
        <small className="font-monospace text-muted">
          {implementation.version ?? ""}
        </small>
      </td>

      <td className="text-center align-middle">
        {implementationResults.erroredCases}
      </td>
      <td className="text-center align-middle">
        {implementationResults.skippedTests}
      </td>
      <td className="text-center align-middle details-required">
        {implementationResults.failedTests + implementationResults.erroredTests}
        <div className="hover-details text-center">
          <p>
            <b>failed</b>: &nbsp;{implementationResults.failedTests}
          </p>
          <p>
            <b>errored</b>: &nbsp;{implementationResults.erroredTests}
          </p>
        </div>
      </td>

      <td className="align-middle p-0">
        {implementationResults.failedTests +
          implementationResults.erroredTests +
          implementationResults.skippedTests >
          0 && (
          <button
            type="button"
            className="btn btn-sm btn-primary"
            onClick={() => setShowDetails(true)}
          >
            Details
          </button>
        )}
      </td>
      <DetailsButtonModal
        show={showDetails}
        handleClose={() => setShowDetails(false)}
        cases={cases}
        implementationResults={implementationResults}
        implementation={implementation}
      />
    </tr>
  );
};

const getImplementationPath = (implResult: ImplementationResults) => {
  const pathSegment = implResult.id.split("/");
  return pathSegment[pathSegment.length - 1];
};

export default ImplementationRow;

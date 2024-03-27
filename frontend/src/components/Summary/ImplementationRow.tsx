import "./ImplementationRow.css";
import { useContext, useState } from "react";
import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { mapLanguage } from "../../data/mapLanguage";
import { useNavigate } from "react-router-dom";
import {
  Case,
  Implementation,
  ImplementationResults,
} from "../../data/parseReportData";
import { ThemeContext } from "../../context/ThemeContext";

const ImplementationRow = ({
  cases,
  id,
  implementation,
  implementationResults,
}: {
  cases: Map<number, Case>;
  id: string;
  implementation: Implementation;
  implementationResults: ImplementationResults;
  key: number;
  index: number;
}) => {
  const { isDarkMode } = useContext(ThemeContext);
  const [showDetails, setShowDetails] = useState(false);
  const navigate = useNavigate();
  const implementationPath = getImplementationPath(id);

  return (
    <tr>
      <th
        className="table-implementation-name align-middle p-0"
        onClick={() => navigate(`/implementations/${implementationPath}`)}
        scope="row"
      >
        <span
          className={`text-decoration-underline ${
            isDarkMode ? "text-primary-emphasis" : "text-primary"
          }`}
        >
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
        {implementationResults.totals.erroredCases}
      </td>
      <td className="text-center align-middle">
        {implementationResults.totals.skippedTests}
      </td>
      <td className="text-center align-middle details-required">
        {implementationResults.totals.failedTests! +
          implementationResults.totals.erroredTests!}
        <div className="hover-details text-center">
          <p>
            <b>failed</b>: &nbsp;{implementationResults.totals.failedTests}
          </p>
          <p>
            <b>errored</b>: &nbsp;{implementationResults.totals.erroredTests}
          </p>
        </div>
      </td>

      <td className="align-middle p-0">
        {implementationResults.totals.failedTests! +
          implementationResults.totals.erroredTests! +
          implementationResults.totals.skippedTests! >
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

const getImplementationPath = (id: string) => {
  const pathSegment = id.split("/");
  return pathSegment[pathSegment.length - 1];
};

export default ImplementationRow;

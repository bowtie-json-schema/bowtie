import "./ImplementationRow.css";
import { useState } from "react";
import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { mapLanguage } from "../../data/mapLanguage";
import { NavLink, useNavigate } from "react-router-dom";
import { Case, ImplementationData } from "../../data/parseReportData";
import { OverlayTrigger, Tooltip } from "react-bootstrap";
const ImplementationRow = ({
  cases,
  implementation,
}: {
  cases: Map<number, Case>;
  implementation: ImplementationData;
  key: number;
  index: number;
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const navigate = useNavigate();
  const implementationPath = getImplementationPath(implementation);

  return (
    <OverlayTrigger
      placement="right"
      overlay={
        <Tooltip className={implementation.isNew ? "" : "d-none"} id="tooltip">
          <strong>Newly added implementation</strong>
        </Tooltip>
      }
    >
      <tr className={implementation.isNew ? "table-success" : ""}>
        <th
          className="table-implementation-name"
          onClick={() => navigate(`/implementations/${implementationPath}`)}
          scope="row"
        >
          <NavLink
            className={implementation.isNew ? "text-primary" : ""}
            to={`/implementations/${implementationPath}`}
          >
            {implementation.metadata.name}
          </NavLink>
          <small
            className={
              "ps-1 " + (implementation.isNew ? "text-dark" : "text-muted")
            }
          >
            {mapLanguage(implementation.metadata.language)}
          </small>
        </th>
        <td>
          <small
            className={
              "font-monospace " +
              (implementation.isNew ? "text-dark" : "text-muted")
            }
          >
            {implementation.metadata.version ?? ""}
          </small>
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
          {implementation.failedTests +
            implementation.erroredTests +
            implementation.skippedTests >
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
          implementation={implementation}
        />
      </tr>
    </OverlayTrigger>
  );
};

const getImplementationPath = (implementation: ImplementationData) => {
  const pathSegment = implementation.id.split("/");
  return pathSegment[pathSegment.length - 1];
};

export default ImplementationRow;

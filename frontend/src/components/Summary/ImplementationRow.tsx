import "./ImplementationRow.css";
import { useState } from "react";
import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { mapLanguage } from "../../data/mapLanguage";
import { NavLink } from "react-router-dom";
import { Case, ImplementationData } from "../../data/parseReportData";
import { Plus } from "react-bootstrap-icons";
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

  const implementationPath = getImplementationPath(implementation);

  return (
    <tr>
      <th scope="row">
        <NavLink to={`/implementations/${implementationPath}`}>
          {implementation.metadata.name}
        </NavLink>
        <small className="text-muted ps-1">
          {mapLanguage(implementation.metadata.language)}
        </small>
      </th>
      <td>
        <small className="font-monospace text-muted">
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
        <button
          type="button"
          className="btn btn-sm btn-primary"
          onClick={() => setShowDetails(true)}
        >
          Details
        </button>
        &nbsp;&nbsp;
        {implementation.isNew && (
          <OverlayTrigger
            placement="right"
            overlay={
              <Tooltip id="tooltip">
                <strong>Newly added Implementation</strong>
              </Tooltip>
            }
          >
            <Plus />
          </OverlayTrigger>
        )}
      </td>
      <DetailsButtonModal
        show={showDetails}
        handleClose={() => setShowDetails(false)}
        cases={cases}
        implementation={implementation}
      />
    </tr>
  );
};

const getImplementationPath = (implementation: ImplementationData) => {
  const pathSegment = implementation.id.split("/");
  return pathSegment[pathSegment.length - 1];
};

export default ImplementationRow;

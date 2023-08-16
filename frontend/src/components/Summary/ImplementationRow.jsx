import "./ImplementationRow.css";
import { useState } from "react";
import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { mapLanguage } from "../../data/mapLanguage";
import { NavLink } from "react-router-dom";

const ImplementationRow = ({ cases, implementation }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getPath = () => {
    const pathSegment = implementation.id.split("/");
    return pathSegment[pathSegment.length - 1];
  };
  return (
    <tr>
      <th scope="row">
        <NavLink to={`/implementations/${getPath()}`}>
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
        {implementation.unsuccessfulTests + implementation.erroredTests}
        <div className="hover-details text-center">
          <p>
            <b>failed</b>:{implementation.unsuccessfulTests}
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

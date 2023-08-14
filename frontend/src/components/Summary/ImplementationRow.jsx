import "./ImplementationRow.css";
import { InfoCircleFill } from "react-bootstrap-icons";
import { useState } from "react";
import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { RunTimeInfoModal } from "../Modals/RunTimeInfoModal";
import { mapLanguage } from "../../data/mapLanguage";
import { NavLink } from "react-router-dom";

const ImplementationRow = ({ cases, implementation }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showRunTimeInfo, setShowRunTimeInfo] = useState(false);

  const getPath = (language, name) => {
    const urlPath = {
      "c++-valijson": "cpp-valijson",
      "dotnet-JsonSchema.Net": "dotnet-jsonschema-net",
      "javascript-ajv": "js-ajv",
      "javascript-hyperjump-jsv": "js-hyperjump",
      "lua-josnschema": "lua-jsonschema",
      "typescript-vscode-json-language-service":
        "ts-vscode-json-languageservice",
    };
    if (`${language}-${name}` in urlPath) {
      return urlPath[`${language}-${name}`];
    } else {
      return `${language}-${name}`;
    }
  };

  return (
    <tr>
      <th scope="row">
        <NavLink
          to={`/implementations/${getPath(
            implementation.metadata.language,
            implementation.metadata.name
          )}`}
        >
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

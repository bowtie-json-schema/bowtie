import { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Popover from "react-bootstrap/Popover";
import Row from "react-bootstrap/Row";

import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { mapLanguage } from "../../data/mapLanguage";
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

  return (
    <tr>
      <th
        scope="row"
        style={{ cursor: "pointer" }}
        className="align-middle p-0"
        onClick={() => navigate(`/implementations/${id}`)}
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

      <OverlayTrigger
        placement="left-end"
        overlay={
          <Popover style={{ border: "1px solid var(--bs-primary)" }}>
            <Popover.Body>
              <Container className="p-0">
                <Row className="d-flex flex-column gap-2">
                  <Col>
                    <b style={{ fontSize: "1rem" }}>failed:</b>&nbsp;
                    <span style={{ fontWeight: "500" }}>
                      {implementationResults.totals.failedTests}
                    </span>
                  </Col>
                  <Col>
                    <b style={{ fontSize: "1rem" }}>errored:</b>&nbsp;
                    <span style={{ fontWeight: "500" }}>
                      {implementationResults.totals.erroredTests}
                    </span>
                  </Col>
                  <Col>
                    <b style={{ fontSize: "1rem" }}>skipped:</b>&nbsp;
                    <span style={{ fontWeight: "500" }}>
                      {implementationResults.totals.skippedTests}
                    </span>
                  </Col>
                </Row>
              </Container>
            </Popover.Body>
          </Popover>
        }
      >
        <td scope="row" colSpan={4} className="text-center">
          {implementationResults.totals.failedTests! +
            implementationResults.totals.erroredTests! +
            implementationResults.totals.skippedTests!}
        </td>
      </OverlayTrigger>

      <td scope="row" colSpan={4} className="align-middle p-0">
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

export default ImplementationRow;

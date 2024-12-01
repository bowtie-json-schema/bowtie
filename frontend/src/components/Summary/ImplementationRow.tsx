import { useContext, useState } from "react";
import { useNavigate } from "react-router";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Popover from "react-bootstrap/Popover";
import Row from "react-bootstrap/Row";

import Implementation from "../../data/Implementation";
import { DetailsButtonModal } from "../Modals/DetailsButtonModal";
import { mapLanguage } from "../../data/mapLanguage";
import { Case, ImplementationResults } from "../../data/parseReportData";
import { ThemeContext } from "../../context/ThemeContext";

interface Props {
  cases: Map<number, Case>;
  implementation: Implementation;
  implementationResults: ImplementationResults;
}

const ImplementationRow = ({
  cases,
  implementation,
  implementationResults,
}: Props) => {
  const { isDarkMode } = useContext(ThemeContext);
  const [showDetails, setShowDetails] = useState(false);
  const navigate = useNavigate();

  return (
    <tr>
      <th
        scope="row"
        style={{ cursor: "pointer" }}
        className="align-middle p-0"
        onClick={() => void navigate(implementation.routePath)}
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
                    <h6 className="fw-bold mb-0">
                      failed:&nbsp;
                      <span className="fw-normal">
                        {implementationResults.totals.failedTests}
                      </span>
                    </h6>
                  </Col>
                  <Col>
                    <h6 className="fw-bold mb-0">
                      errored:&nbsp;
                      <span className="fw-normal">
                        {implementationResults.totals.erroredTests}
                      </span>
                    </h6>
                  </Col>
                  <Col>
                    <h6 className="fw-bold mb-0">
                      skipped:&nbsp;
                      <span className="fw-normal">
                        {implementationResults.totals.skippedTests}
                      </span>
                    </h6>
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

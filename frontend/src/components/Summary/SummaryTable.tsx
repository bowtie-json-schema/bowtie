import { useMemo } from "react";
import Table from "react-bootstrap/Table";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Popover from "react-bootstrap/Popover";
import Row from "react-bootstrap/Row";

import ImplementationRow from "./ImplementationRow";
import { ReportData, calculateTotals } from "../../data/parseReportData";

const SummaryTable = ({ reportData }: { reportData: ReportData }) => {
  const totals = useMemo(() => calculateTotals(reportData), [reportData]);
  return (
    <Table hover responsive>
      <thead>
        <tr>
          <th
            scope="col"
            colSpan={2}
            rowSpan={2}
            className="text-center align-middle"
          >
            implementation
          </th>
          <th scope="col" colSpan={2} className="text-center">
            <span className="text-muted">cases ({reportData.cases.size})</span>
          </th>
          <th scope="col" colSpan={2} className="text-center">
            <span className="text-muted">tests ({totals.totalTests})</span>
          </th>
        </tr>
        <tr>
          <OverlayTrigger
            placement="left-start"
            overlay={
              <Popover style={{ border: "1px solid var(--bs-primary)" }}>
                <Popover.Body>
                  <Container className="p-0 text-center">
                    <Row className="d-flex flex-column gap-3">
                      <Col>
                        <h6 className="fw-bold mb-0">failed</h6>
                        <span className="fw-medium">
                          implementation worked successfully but got the wrong
                          answer
                        </span>
                      </Col>
                      <Col>
                        <h6 className="fw-bold mb-0">errored</h6>
                        <span className="fw-medium">
                          implementation crashed when trying to calculate an
                          answer
                        </span>
                      </Col>
                      <Col>
                        <h6 className="fw-bold mb-0">skipped</h6>
                        <span className="fw-medium">
                          implementation skipped the test (typically because it
                          is a known bug)
                        </span>
                      </Col>
                    </Row>
                  </Container>
                </Popover.Body>
              </Popover>
            }
          >
            <th
              scope="col"
              colSpan={4}
              className="table-bordered text-center details-required"
            >
              unsuccessful
            </th>
          </OverlayTrigger>
        </tr>
      </thead>
      <tbody className="table-group-divider">
        {Array.from(reportData.implementationsResults.entries())
          .sort(
            ([, a], [, b]) =>
              a.totals.failedTests! +
              a.totals.erroredTests! +
              a.totals.skippedTests! -
              b.totals.failedTests! -
              b.totals.erroredTests! -
              b.totals.skippedTests!,
          )
          .map(([id, implResults]) => (
            <ImplementationRow
              key={id}
              cases={reportData.cases}
              implementation={reportData.runMetadata.implementations.get(id)!}
              implementationResults={implResults}
            />
          ))}
      </tbody>
    </Table>
  );
};

export default SummaryTable;

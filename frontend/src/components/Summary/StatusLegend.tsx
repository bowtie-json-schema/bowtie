import { ReactElement } from "react";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Popover from "react-bootstrap/Popover";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

interface StatusLegendProps {
  children: ReactElement;
}

const StatusLegend = ({ children }: StatusLegendProps) => {
  return (
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
                    implementation worked successfully but got the wrong answer
                  </span>
                </Col>
                <Col>
                  <h6 className="fw-bold mb-0">errored</h6>
                  <span className="fw-medium">
                    implementation crashed when trying to calculate an answer
                  </span>
                </Col>
                <Col>
                  <h6 className="fw-bold mb-0">skipped</h6>
                  <span className="fw-medium">
                    implementation skipped the test (typically because it is a
                    known bug)
                  </span>
                </Col>
              </Row>
            </Container>
          </Popover.Body>
        </Popover>
      }
    >
      {children}
    </OverlayTrigger>
  );
};

export default StatusLegend;
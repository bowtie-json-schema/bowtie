import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import Col from "react-bootstrap/Col";
import Card from "react-bootstrap/Card";
import { mapLanguage } from "../../data/mapLanguage";
import {
  Case,
  Implementation,
  ImplementationResults,
} from "../../data/parseReportData";
import SchemaDisplay from "../Cases/SchemaDisplay";
import { useId } from "react";

export const DetailsButtonModal = ({
  show,
  handleClose,
  cases,
  implementationResults,
  implementation,
}: {
  show: boolean;
  handleClose: () => void;
  cases: Map<number, Case>;
  implementationResults: ImplementationResults;
  implementation: Implementation;
}) => {
  const modalBodyId = useId();
  const failedResults: JSX.Element[] = [];
  Array.from(implementationResults.caseResults.entries()).forEach(
    ([seq, results]) => {
      const caseData = cases.get(seq)!;
      for (let i = 0; i < results.length; i++) {
        const result = results[i];
        if (result.state === "successful") {
          continue;
        }

        let message;
        if (result.state === "skipped" || result.state === "errored") {
          message = implementationResults.caseResults.get(seq)![i].message!;
        } else if (result.valid) {
          message = "Unexpectedly valid";
        } else {
          message = "Unexpectedly invalid";
        }
        const borderClass =
          result.state === "skipped" ? "border-warning" : "border-danger";
        failedResults.push(
          <DetailItem
            key={`${seq}-${i}`}
            title={caseData.description}
            description={caseData.tests[i].description}
            schema={caseData.schema}
            instance={caseData.tests[i].instance}
            message={message}
            borderClass={borderClass}
            modalBodyId={modalBodyId}
          />
        );
      }
    }
  );
  return (
    <Modal show={show} onHide={handleClose} fullscreen={true}>
      <Modal.Header closeButton>
        <Modal.Title>
          <label className="me-1">Unsuccessful Tests:</label>
          <b>{implementation.name}</b>
          <small className="text-muted ps-2">
            {mapLanguage(implementation.language)}
          </small>
        </Modal.Title>
      </Modal.Header>
      <Modal.Body id={modalBodyId}>
        <div className="row row-cols-1 row-cols-md-2 g-4">{failedResults}</div>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

const DetailItem = ({
  title,
  description,
  message,
  schema,
  instance,
  borderClass,
  modalBodyId,
}: {
  title: string;
  description: string;
  message: string;
  schema: Record<string, unknown> | boolean;
  instance: unknown;
  borderClass: string;
  modalBodyId: string;
}) => {
  return (
    <Col>
      <Card className={`mb-3 ${borderClass}`}>
        <Card.Body>
          <Card.Title>
            <span>Case: {title}</span>
          </Card.Title>
          <Card.Text>
            <span>Test: {description}</span>
          </Card.Text>
          <SchemaDisplay
            schema={schema}
            instance={instance}
            modalBodyId={modalBodyId}
          />
        </Card.Body>
        <Card.Footer className="text-muted text-center">
          <span>Result: {message}</span>
        </Card.Footer>
      </Card>
    </Col>
  );
};

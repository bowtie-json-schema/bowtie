import { Button, Modal } from "react-bootstrap";
import { mapLanguage } from "../../data/mapLanguage";
import {
  Case,
  Implementation,
  ImplementationResults,
} from "../../data/parseReportData";
import SchemaDisplay from "../Cases/SchemaDisplay";

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
  const failedResults: JSX.Element[] = [];
  Array.from(implementationResults.cases.entries()).forEach(
    ([seq, results]) => {
      const caseData = cases.get(seq)!;
      for (let i = 0; i < results.length; i++) {
        const result = results[i];
        if (result.state === "successful") {
          continue;
        }

        let message;
        if (result.state === "skipped" || result.state === "errored") {
          message = implementationResults.cases.get(seq)![i].message!;
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
      <Modal.Body>
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
}: {
  title: string;
  description: string;
  message: string;
  schema: Record<string, unknown> | boolean;
  instance: unknown;
  borderClass: string;
}) => {
  return (
    <div className="col">
      <div className={`card mb-3 ${borderClass}`}>
        <div className="card-body">
          <h5 className="card-title">
            <label className="me-1">Case:</label>
            {title}
          </h5>
          <p className="card-text">
            <label className="me-1">Test:</label>
            {description}
          </p>
          <SchemaDisplay schema={schema} instance={instance} />
        </div>
        <div className="card-footer text-muted text-center">
          <label className="me-1">Result:</label>
          {message}
        </div>
      </div>
    </div>
  );
};

import { Button, Modal } from "react-bootstrap";
import { mapLanguage } from "../../data/mapLanguage";
import { Case, ImplementationData } from "../../data/parseReportData";

export const DetailsButtonModal = ({
  show,
  handleClose,
  cases,
  implementation,
}: {
  show: boolean;
  handleClose: () => void;
  cases: Map<number, Case>;
  implementation: ImplementationData;
}) => {
  const failedResults: JSX.Element[] = [];
  Array.from(implementation.cases.entries()).forEach(([seq, results]) => {
    const caseData = cases.get(seq)!;
    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      if (result.state === "successful") {
        continue;
      }

      let message;
      if (result.state === "skipped" || result.state === "errored") {
        message = implementation.cases.get(seq)![i].message!;
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
        />,
      );
    }
  });
  return (
    <Modal show={show} onHide={handleClose} fullscreen={true}>
      <Modal.Header closeButton>
        <Modal.Title>
          <small className="text-muted ps-2">
            JSON Schema test cases that need attention : &nbsp;
          </small>
          <b>{implementation.metadata.name}</b>
          <small className="text-muted ps-2">
            {mapLanguage(implementation.metadata.language)}
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
  const schemaFormatted = JSON.stringify(schema, null, 2);
  const instanceFormatted = JSON.stringify(instance, null, 2);
  return (
    <div className="col">
      <div className={`card mb-3 ${borderClass}`}>
        <div className="card-body">
          <h5 className="card-title">Case : {title}</h5>
          <p className="card-text">Test: {description}</p>
          <div className="card-body">
            <pre id="schema-code">Schema: {schemaFormatted}</pre>
          </div>
          <div className="card-body">
            <pre id="schema-code">Instance: {instanceFormatted}</pre>
          </div>
        </div>
        <div className="card-footer text-muted text-center">
          Result: {message}
        </div>
      </div>
    </div>
  );
};

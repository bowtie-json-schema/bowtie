import { Button, Modal } from "react-bootstrap";
import { mapLanguage } from "../../data/mapLanguage";

export const DetailsButtonModal = ({
  show,
  handleClose,
  cases,
  implementation,
}) => {
  const failedResults = [];
  Array.from(implementation.cases.entries()).forEach(([seq, results]) => {
    const caseData = cases.get(seq);
    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      if (result.state === "successful") {
        continue;
      }

      let message;
      if (result.state === "skipped" || result.state === "errored") {
        message = implementation.cases.get(seq)[i].message;
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

const DetailItem = ({ title, description, message, borderClass }) => {
  return (
    <div className="col">
      <div className={`card mb-3 ${borderClass}`}>
        <div className="card-body">
          <h5 className="card-title">{title}</h5>
          <p className="card-text">{description}</p>
        </div>
        <div className="card-footer text-muted text-center">{message}</div>
      </div>
    </div>
  );
};

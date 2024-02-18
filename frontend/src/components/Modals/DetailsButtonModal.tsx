import { Button, Modal } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
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
          eventKey={seq.toString()}
          closeModal={handleClose}
          title={caseData.description}
          description={caseData.tests[i].description}
          message={message}
          borderClass={borderClass}
        />
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

const DetailItem = ({
  eventKey,
  closeModal,
  title,
  description,
  message,
  borderClass,
}: {
  eventKey: string;
  closeModal: VoidFunction;
  title: string;
  description: string;
  message: string;
  borderClass: string;
}) => {
  const navigate = useNavigate();

  return (
    <div className="col">
      <div
        className={`card mb-3 ${borderClass}`}
        style={{ cursor: "pointer" }}
        onClick={() => {
          navigate(`#${eventKey}`);
          closeModal();
        }}
      >
        <div className="card-body">
          <h5 className="card-title">{title}</h5>
          <p className="card-text">{description}</p>
        </div>
        <div className="card-footer text-muted text-center">{message}</div>
      </div>
    </div>
  );
};

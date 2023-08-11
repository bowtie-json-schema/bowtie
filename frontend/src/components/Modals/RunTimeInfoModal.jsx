import { Button, Modal } from "react-bootstrap";
import { mapLanguage } from "../../data/mapLanguage";

export const RunTimeInfoModal = ({ show, handleClose, implementation }) => {
  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>
          <b>{implementation.metadata.name}</b>
          <small className="text-muted ps-2">
            {mapLanguage(implementation.metadata.language)}
          </small>
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {implementation.metadata.os_version && (
          <p>
            <strong>OS Version: </strong>
            {implementation.metadata.os_version || ""}
          </p>
        )}
        {implementation.metadata.os && (
          <p>
            <strong>OS: </strong>
            {implementation.metadata.os || ""}
          </p>
        )}
        {implementation.metadata.language && (
          <p>
            <strong>Language: </strong>
            {mapLanguage(implementation.metadata.language)}
          </p>
        )}
        {implementation.metadata.language_version && (
          <p>
            <strong>Language Version: </strong>
            {implementation.metadata.language_version || ""}
          </p>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

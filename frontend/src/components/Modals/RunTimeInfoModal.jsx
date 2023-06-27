export const RunTimeInfoModal = ({ reportData }) => {
  return (
    <>
      {summary.implementations.map((implementation, index) => (
        <div
          className="modal fade"
          role="dialog"
          id={`implementation-${index}-runtime-info`}
          tabIndex="-1"
          aria-labelledby={`implementation-${index}-runtime-info-label`}
          aria-hidden="true"
          key={index}
        >
          <div className="modal-dialog" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5
                  className="modal-title"
                  id={`implementation-${index}-runtime-info-label`}
                >
                  <b>{implementation.name + " "}</b>
                  <small className="text-muted">
                    {" "}
                    {implementation.language}
                  </small>
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  data-bs-dismiss="modal"
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">
                {implementation.os_version && (
                  <p>
                    <strong>OS Version: </strong>
                    {implementation.os_version || ""}
                  </p>
                )}
                {implementation.os && (
                  <p>
                    <strong>OS: </strong>
                    {implementation.os || ""}
                  </p>
                )}
                {implementation.language && (
                  <p>
                    <strong>Language: </strong>
                    {implementation.language}
                  </p>
                )}
                {implementation.language_version && (
                  <p>
                    <strong>Language Version: </strong>
                    {implementation.language_version || ""}
                  </p>
                )}
              </div>
              <div className="modal-footer m-2 p-0">
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  data-bs-dismiss="modal"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      ))}
    </>
  );
};

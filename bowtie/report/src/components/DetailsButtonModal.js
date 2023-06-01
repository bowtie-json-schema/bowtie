export const DetailsButtonModal = ({ summary }) => {
  return (
    <>
      {summary.implementations.map((implementation, index) => (
        <div
          className="modal fade"
          id={`implementation-${index}-details`}
          tabIndex="-1"
          aria-labelledby={`implementation-${index}-details-label`}
          aria-hidden="true"
          key={index}
        >
          <div className="modal-dialog modal-fullscreen">
            <div className="modal-content">
              <div className="modal-header">
                <h1
                  className="modal-title fs-5"
                  id={`implementation-${index}-details-label`}
                >
                  <b>{implementation.name + " "}</b>
                  <small className="text-muted">
                    {implementation.language}
                  </small>
                </h1>
                <button
                  type="button"
                  className="btn-close"
                  data-bs-dismiss="modal"
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">
                <div className="row row-cols-1 row-cols-md-2 g-4">
                  {/* {summary
                    .flat_results()
                    .map(([seq, description, schema, registry, results]) =>
                      results.map(([test, test_results]) => {
                        const [implementation_result, incorrect] =
                          test_results.get(
                            implementation.image,
                            ({ valid: null }, true)
                          );

                        if (incorrect === "skipped") {
                          return (
                            <div className="col" key={seq}>
                              <div className="card border-warning mb-3">
                                <div className="card-body">
                                  <h5 className="card-title">{description}</h5>
                                  <p className="card-text">
                                    {test.description}
                                  </p>
                                </div>
                                <div className="card-footer text-muted text-center">
                                  {implementation_result}
                                </div>
                              </div>
                            </div>
                          );
                        } else if (incorrect === "errored") {
                          return (
                            <div className="col" key={seq}>
                              <div className="card border-danger mb-3">
                                <div className="card-body">
                                  <h5 className="card-title">{description}</h5>
                                  <p className="card-text">
                                    {test.description}
                                  </p>
                                </div>
                                <div className="card-footer text-muted text-center">
                                  {implementation_result}
                                </div>
                              </div>
                            </div>
                          );
                        } else if (incorrect) {
                          return (
                            <div className="col" key={seq}>
                              <div className="card border-danger mb-3">
                                <div className="card-body">
                                  <h5 className="card-title">{description}</h5>
                                  <p className="card-text">
                                    {test.description}
                                  </p>
                                </div>
                                <div className="card-footer text-muted text-center">
                                  Unexpectedly{" "}
                                  {implementation_result.valid === true
                                    ? "valid"
                                    : implementation_result.valid === false
                                    ? "invalid"
                                    : "errored"}
                                </div>
                              </div>
                            </div>
                          );
                        }
                      })
                    )} */}
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
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

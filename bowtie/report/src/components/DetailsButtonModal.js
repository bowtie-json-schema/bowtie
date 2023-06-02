export const DetailsButtonModal = ({ lines, summary }) => {
  const implementationArray = lines.filter((element) => element.implementation);
  const caseArray = lines.filter((element) => element.case);

  // console.log(implementationArray)
  // console.log(caseArray)
  function TestStatus(implementationImage) {
    let testStatusArray;
    var arrayOfSeqCases = [];
    implementationArray.forEach((seqImplementation) => {
      if (seqImplementation.implementation === implementationImage) {
        // var caseResults = [];
        if (seqImplementation.skipped) {
          var seq = seqImplementation.seq;
          caseArray.forEach((seqCase) => {
            if (seqCase.seq == seq) {
              var hasResultsArray = false;
              arrayOfSeqCases.push(seqCase);
              testStatusArray = ["skipped", seqImplementation, hasResultsArray];
            }
          });
        } else if (seqImplementation.results) {
          var caseResults = seqImplementation.results.filter(
            (element) => element.skipped
          );
          // console.log(caseResults)
          if (caseResults.length > 0) {
            var seq = seqImplementation.seq;
            caseArray.forEach((seqCase) => {
              if (seqCase.seq == seq) {
                var hasResultsArray = true;
                arrayOfSeqCases.push(seqCase);
                testStatusArray = [
                  "skipped",
                  seqImplementation,
                  hasResultsArray,
                ];
              }
            });
          }
        } else if (seqImplementation.caught) {
          let seq = seqImplementation.seq;
          // console.log(seq)
          caseArray.forEach((seqCase) => {
            if (seqCase.seq == seq) {
              var hasResultsArray = true;
              arrayOfSeqCases.push(seqCase);
              testStatusArray = ["errored", seqImplementation, hasResultsArray];
            }
          });
        } else if (seqImplementation.results) {
          var caseResults = seqImplementation.results.filter(
            (seqImplementation) => seqImplementation.context
          );
          // console.log(caseResults);
          if (caseResults.errored) {
            let seq = seqImplementation.seq;
            caseArray.forEach((each) => {
              if (each.seq === seq) {
                var hasResultsArray = true;
                arrayOfSeqCases.push(seqCase);
                testStatusArray = [
                  "errored",
                  seqImplementation,
                  hasResultsArray,
                ];
              }
            });
          }
        }
      }
    });
    return [testStatusArray, arrayOfSeqCases];
  }

  return (
    <>
      {summary.implementations.map((implementation, index) => {
        const result = TestStatus(implementation.image);
        const [testStatusArray, arrayOfSeqCases] = result;
        {
          /* console.log(arrayOfSeqCases); */
        }
        if (Array.isArray(testStatusArray)) {
          const [testStatus, seqImplementation, hasResultsArray] =
            testStatusArray;
          {
            /* console.log(seqImplementation); */
          }
          return (
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
                      {arrayOfSeqCases.map((seqCase, i) =>
                        seqCase.case.tests.map((eachTest, index) => {
                          if (testStatus === "skipped") {
                            return (
                              <div
                                className="col"
                                key={`${seqCase.seq}${index}`}
                              >
                                <div className="card border-warning mb-3">
                                  <div className="card-body">
                                    <h5 className="card-title">
                                      {seqCase.case.description}
                                    </h5>
                                    <p className="card-text">
                                      {eachTest.description}
                                    </p>
                                  </div>
                                  <div className="card-footer text-muted text-center">
                                    {seqImplementation.message}
                                  </div>
                                </div>
                              </div>
                            );
                          } else if (testStatus === "errored") {
                            return (
                              <div
                                className="col"
                                key={`${seqCase.seq}${index}`}
                              >
                                <div className="card border-danger mb-3">
                                  <div className="card-body">
                                    <h5 className="card-title">
                                      {seqCase.case.description}
                                    </h5>
                                    <p className="card-text">
                                      {eachTest.description}
                                    </p>
                                  </div>
                                  <div className="card-footer text-muted text-center">
                                    {seqImplementation.message}
                                  </div>
                                </div>
                              </div>
                            );
                          }
                        })
                      )}
                      {/* {summary
                    .flat_results()
                    .map(([seq, description, schema, registry, results]) =>
                      results.map(([test, test_results]) => {
                        const [implementation_result, incorrect] =
                          test_results.get(
                            implementation.image,
                            ({ valid: null }, true)
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
          );
        }
      })}
    </>
  );
};

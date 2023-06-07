import DetailsModalCard from "../DetailsModalCard";

export const DetailsButtonModal = ({ lines, summary }) => {
  const implementationArray = lines.filter((element) => element.implementation);
  const caseArray = lines.filter((element) => element.case);

  function results(implementationImage) {
    var implementationTests = implementationArray.filter(
      (obj) => obj.implementation === implementationImage
    );

    var dataArray = [];
    implementationTests.forEach((testImplementation) => {
      if (testImplementation.skipped && testImplementation.skipped === true) {
        var testResult = "directSkipped";
        var testCase = caseArray.find(
          (obj) => obj.seq === testImplementation.seq
        );
        dataArray.push([testResult, testCase, testImplementation]);
      } else if (testImplementation.results && testImplementation.expected) {
        if (testImplementation.results.every((obj) => obj.skipped === true)) {
          var testResult = "skipped";
          var testCase = caseArray.find(
            (obj) => obj.seq === testImplementation.seq
          );
          // console.log(testImplementation)
          // console.log(testCase)
          // console.log(testResult)
          dataArray.push([testResult, testCase, testImplementation]);
        }
      }
    });
    return dataArray;
  }

  return (
    <>
      {summary.implementations.map((implementation, index) => {
        var result = results(implementation.image);
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
                    {result.map((eachResult, i) => {
                      var [testResult, testCase, testImplementation] =
                        eachResult;
                      if (testResult === "skipped") {
                        return testCase.case.tests.map((test, index) => {
                          return (
                            <div
                              className="col"
                              key={`${testCase.seq}${index}`}
                            >
                              <div className="card border-warning mb-3">
                                <div className="card-body">
                                  <h5 className="card-title">
                                    {testCase.case.description}
                                  </h5>
                                  <p className="card-text">
                                    {test.description}
                                  </p>
                                </div>
                                <div className="card-footer text-muted text-center">
                                  {testImplementation.results[index].message}
                                </div>
                              </div>
                            </div>
                          );
                        });
                      } else if (testResult === "directSkipped") {
                        return testCase.case.tests.map((test, index) => {
                          return (
                            <div
                              className="col"
                              key={`${testCase.seq}${index}`}
                            >
                              <div className="card border-warning mb-3">
                                <div className="card-body">
                                  <h5 className="card-title">
                                    {testCase.case.description}
                                  </h5>
                                  <p className="card-text">
                                    {test.description}
                                  </p>
                                </div>
                                <div className="card-footer text-muted text-center">
                                  {testImplementation.message}
                                </div>
                              </div>
                            </div>
                          );
                        });
                      }
                    })}
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
      })}
    </>
  );
};

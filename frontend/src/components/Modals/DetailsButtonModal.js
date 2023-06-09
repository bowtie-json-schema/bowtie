export const DetailsButtonModal = ({ lines, summary }) => {
  const implementationArray = lines.filter((element) => element.implementation);
  const caseArray = lines.filter((element) => element.case);

  function results(implementationImage) {
    let implementationTests = implementationArray.filter(
      (obj) => obj.implementation === implementationImage,
    );

    let dataArray = [];
    implementationTests.forEach((testImplementation) => {
      if (testImplementation.skipped === true) {
        const testResult = "directSkipped";
        const testCase = caseArray.find(
          (obj) => obj.seq === testImplementation.seq,
        );
        dataArray.push([testResult, testCase, testImplementation]);
      }
      if (
        testImplementation.caught === true ||
        testImplementation.caught === false
      ) {
        const testResult = "caught";
        const testCase = caseArray.find(
          (obj) => obj.seq === testImplementation.seq,
        );
        dataArray.push([testResult, testCase, testImplementation]);
      }
      if (testImplementation.results && testImplementation.expected) {
        if (testImplementation.results.every((obj) => obj.skipped === true)) {
          const testResult = "skipped";
          const testCase = caseArray.find(
            (obj) => obj.seq === testImplementation.seq,
          );
          dataArray.push([testResult, testCase, testImplementation]);
        }
        if (
          testImplementation.results.every(
            (element) =>
              typeof element === "object" &&
              Object.keys(element).length === 1 &&
              "valid" in element,
          )
        ) {
          for (
            let index = 0;
            index < testImplementation.results.length;
            index++
          ) {
            if (
              testImplementation.results[index].valid !==
              testImplementation.expected[index]
            ) {
              let validity = [];
              if (testImplementation.expected[index] === false) {
                validity.push(index);
                const testResult = "unexpectedlyValid";
                const testCase = caseArray.find(
                  (obj) => obj.seq === testImplementation.seq,
                );
                dataArray.push([
                  testResult,
                  testCase,
                  testImplementation,
                  validity,
                ]);
              } else if (testImplementation.expected[index] === true) {
                validity.push(index);
                const testResult = "unexpectedlyInvalid";
                const testCase = caseArray.find(
                  (obj) => obj.seq === testImplementation.seq,
                );
                dataArray.push([
                  testResult,
                  testCase,
                  testImplementation,
                  validity,
                ]);
              }
            }
          }
        }
      }
    });
    return dataArray;
  }

  return (
    <>
      {summary.implementations.map((implementation, index) => {
        let result = results(implementation.image);
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
                      let [testResult, testCase, testImplementation, validity] =
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
                      }
                      if (testResult === "directSkipped") {
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
                      if (testResult === "caught") {
                        return testCase.case.tests.map((test, index) => {
                          return (
                            <div
                              className="col"
                              key={`${testCase.seq}${index}`}
                            >
                              <div className="card border-danger mb-3">
                                <div className="card-body">
                                  <h5 className="card-title">
                                    {testCase.case.description}
                                  </h5>
                                  <p className="card-text">
                                    {test.description}
                                  </p>
                                </div>
                                <div className="card-footer text-muted text-center">
                                  Unexpectedly errored
                                </div>
                              </div>
                            </div>
                          );
                        });
                      }
                      if (testResult === "unexpectedlyValid") {
                        return testCase.case.tests.map((test, index) => {
                          if (validity.includes(index)) {
                            return (
                              <div
                                className="col"
                                key={`${testCase.seq}${index}`}
                              >
                                <div className="card border-danger mb-3">
                                  <div className="card-body">
                                    <h5 className="card-title">
                                      {testCase.case.description}
                                    </h5>
                                    <p className="card-text">
                                      {test.description}
                                    </p>
                                  </div>
                                  <div className="card-footer text-muted text-center">
                                    Unexpectedly valid
                                  </div>
                                </div>
                              </div>
                            );
                          }
                        });
                      }
                      if (testResult === "unexpectedlyInvalid") {
                        return testCase.case.tests.map((test, index) => {
                          if (validity.includes(index)) {
                            return (
                              <div
                                className="col"
                                key={`${testCase.seq}${index}`}
                              >
                                <div className="card border-danger mb-3">
                                  <div className="card-body">
                                    <h5 className="card-title">
                                      {testCase.case.description}
                                    </h5>
                                    <p className="card-text">
                                      {test.description}
                                    </p>
                                  </div>
                                  <div className="card-footer text-muted text-center">
                                    Unexpectedly invalid
                                  </div>
                                </div>
                              </div>
                            );
                          }
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

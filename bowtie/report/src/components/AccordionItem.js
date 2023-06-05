import AccordionSvg from "./AccordionSvg";

const AccordionItem = ({
  lines,
  eachCase,
  implementations,
  caseImplementation,
}) => {
  const caseArray = lines.filter((obj) => obj.case);
  const implementationArray = lines.filter((obj) => obj.implementation);
  const seq = eachCase.seq;
  const description = eachCase.case.description;
  const schema = eachCase.case.schema;
  const registry = eachCase.case.registry;
  const tests = eachCase.case.tests;

  function result(implementation) {
    var testResult;
    if (implementation.skipped && implementation.skipped == true) {
      return (testResult = "skipped");
    } else if (implementation.results) {
      var caseResults = implementation.results.filter(
        (element) => element.skipped
      );
      if (caseResults.length > 0) {
        return (testResult = "skipped");
      }
    } else if (implementation.caught && implementation.caught == true) {
      return (testResult = "errored");
    } else if (implementation.results) {
      if (implementation.results.every((each) =>
          typeof each === "object" && each.hasOwnProperty("errored")
      )) {
        return (testResult = "errored");
      }
    } else {
      
    }
  }
  return (
    <div className="accordion-item">
      <h2 className="accordion-header" id={`case-${seq}-heading`}>
        <button
          className="accordion-button collapsed"
          type="button"
          // onClick={() =>
          //   schemaDisplay(
          //     `accordion-body${seq}`,
          //     JSON.stringify(schema, null, 2),
          //     "schema-code",
          //     `row-${seq}`
          //   )
          // }
          data-bs-toggle="collapse"
          data-bs-target={`#case-${seq}`}
          aria-expanded="false"
          aria-controls={`case-${seq}`}
        >
          <a href="#schema" className="text-decoration-none">
            {description}
          </a>
        </button>
      </h2>
      <div
        id={`case-${seq}`}
        className="accordion-collapse collapse"
        aria-labelledby={`case-${seq}-heading`}
        data-bs-parent="#cases"
      >
        <div id={`accordion-body${seq}`} className="accordion-body">
          <table className="table table-hover">
            <thead>
              <tr>
                <td scope="col">
                  <b>Tests</b>
                </td>
                {implementations.map((implementation) => (
                  <td
                    className="text-center"
                    scope="col"
                    key={implementation.name + implementation.language}
                  >
                    <b>{implementation.name + " "}</b>
                    <small className="text-muted">
                      {implementation.language}
                    </small>
                  </td>
                ))}
              </tr>
            </thead>
            <tbody>
              {tests.map((test, index) => (
                <tr
                  className={`row-${seq}`}
                  key={index}
                  // onClick={() =>
                  //   displayCode(
                  //     JSON.stringify(testResult.instance, null, 2),
                  //     "instance-info"
                  //   )
                  // }
                >
                  <td>
                    <a href="#schema" className="text-decoration-none">
                      {test.description}
                    </a>
                  </td>
                  {implementations.map((impl, i) => {
                    let testCase;
                    var implementation = caseImplementation.find(
                      (each) => each.implementation === impl.image
                    );
                    var testResult = result(implementation);
                    if (testResult == "skipped") {
                      return (
                        <td key={i} className="text-center text-bg-warning">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            fill="currentColor"
                            className="bi bi-exclamation-octagon"
                            viewBox="0 0 16 16"
                          >
                            <path d="M4.54.146A.5.5 0 0 1 4.893 0h6.214a.5.5 0 0 1 .353.146l4.394 4.394a.5.5 0 0 1 .146.353v6.214a.5.5 0 0 1-.146.353l-4.394 4.394a.5.5 0 0 1-.353.146H4.893a.5.5 0 0 1-.353-.146L.146 11.46A.5.5 0 0 1 0 11.107V4.893a.5.5 0 0 1 .146-.353L4.54.146zM5.1 1 1 5.1v5.8L5.1 15h5.8l4.1-4.1V5.1L10.9 1H5.1z" />
                            <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z" />
                          </svg>
                        </td>
                      );
                    } else if (testResult == "errored") {
                      return (
                        <td key={i} className="text-center text-bg-danger">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            fill="currentColor"
                            className="bi bi-exclamation-octagon"
                            viewBox="0 0 16 16"
                          >
                            <path d="M4.54.146A.5.5 0 0 1 4.893 0h6.214a.5.5 0 0 1 .353.146l4.394 4.394a.5.5 0 0 1 .146.353v6.214a.5.5 0 0 1-.146.353l-4.394 4.394a.5.5 0 0 1-.353.146H4.893a.5.5 0 0 1-.353-.146L.146 11.46A.5.5 0 0 1 0 11.107V4.893a.5.5 0 0 1 .146-.353L4.54.146zM5.1 1 1 5.1v5.8L5.1 15h5.8l4.1-4.1V5.1L10.9 1H5.1z" />
                            <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z" />
                          </svg>
                        </td>
                      );
                    } else {
                      return <td key={i}>Agni</td>;
                    }

                    {
                      /* console.log(testCase) */
                    }
                    {
                      /* return testCase; */
                    }

                    {
                      /* if (implementation.results && implementation.expected ) {
                      if (
                        implementation.results.every((element) => typeof element === "object" && Object.keys(element).length === 1 && "valid" in element)) {
                        for ( let i = 0; i < implementation.results.length; i++) {
                          if ( implementation.results[i].valid === implementation.expected[i]) {
                            testCase = "passed";
                          }
                        }
                      }

                    } else if (implementation.results && implementation.expected ) {
                      if (
                        implementation.results.every((element) => typeof element === "object" && Object.keys(element).length === 1 && "valid" in element)) {
                        for ( let i = 0; i < implementation.results.length; i++) {
                          if ( implementation.results[i].valid === implementation.expected[i]) {
                            testCase = "passed";
                          }
                        }
                      }
                    } */
                    }
                    {
                      /* if (testCase === "faileds") {
                      return (
                        <td key={index} className="text-center">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            fill="currentColor"
                            className="bi bi-x-circle-fill"
                            viewBox="0 0 16 16"
                          >
                            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z" />
                          </svg>
                        </td>
                      );
                    } */
                    }
                    {
                      /* if (testCase === "passed") {
                      return (
                        <td key={index} className="text-center">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            fill="currentColor"
                            className="bi bi-check-circle-fill"
                            viewBox="0 0 16 16"
                          >
                            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z" />
                          </svg>
                        </td>
                      );
                    } */
                    }
                    if (testCase === "skipped") {
                      return (
                        <td key={i} className="text-center text-bg-warning">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            fill="currentColor"
                            className="bi bi-exclamation-octagon"
                            viewBox="0 0 16 16"
                          >
                            <path d="M4.54.146A.5.5 0 0 1 4.893 0h6.214a.5.5 0 0 1 .353.146l4.394 4.394a.5.5 0 0 1 .146.353v6.214a.5.5 0 0 1-.146.353l-4.394 4.394a.5.5 0 0 1-.353.146H4.893a.5.5 0 0 1-.353-.146L.146 11.46A.5.5 0 0 1 0 11.107V4.893a.5.5 0 0 1 .146-.353L4.54.146zM5.1 1 1 5.1v5.8L5.1 15h5.8l4.1-4.1V5.1L10.9 1H5.1z" />
                            <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z" />
                          </svg>
                        </td>
                      );
                    }
                    {
                      /* if (element.skipped) {
                          if (eachCase.seq == element.seq) {
                            console.log(element);
                            testCase = "skipped";
                          }
                        } else if (element.results) {
                          var caseResults = element.results.filter(
                            (element) => element.skipped
                          );
                          if (caseResults.length > 0) {
                            if (eachCase.seq == seq) {
                              console.log(element);
                              testCase = "skipped";
                            }
                          }
                        } */
                    }

                    {
                      /* return (
                      <td key={index}>
                        {testCase == "skipped" ? (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            fill="currentColor"
                            className="bi bi-exclamation-octagon"
                            viewBox="0 0 16 16"
                          >
                            <path d="M4.54.146A.5.5 0 0 1 4.893 0h6.214a.5.5 0 0 1 .353.146l4.394 4.394a.5.5 0 0 1 .146.353v6.214a.5.5 0 0 1-.146.353l-4.394 4.394a.5.5 0 0 1-.353.146H4.893a.5.5 0 0 1-.353-.146L.146 11.46A.5.5 0 0 1 0 11.107V4.893a.5.5 0 0 1 .146-.353L4.54.146zM5.1 1 1 5.1v5.8L5.1 15h5.8l4.1-4.1V5.1L10.9 1H5.1z" />
                            <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z" />
                          </svg>
                        ) : testCase == "failed" ? (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            fill="currentColor"
                            className="bi bi-x-circle-fill"
                            viewBox="0 0 16 16"
                          >
                            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z" />
                          </svg>
                        ) : null}
                      </td>
                    ); */
                    }
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AccordionItem;

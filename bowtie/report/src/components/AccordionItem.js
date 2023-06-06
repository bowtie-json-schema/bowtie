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

  function result(index, implementation) {
    var testResult;
    // console.log(implementation)

    if (implementation.skipped && implementation.skipped == true) {
      return (testResult = "skipped");
    } else if (implementation.caught && implementation.caught == true) {
      return (testResult = "errored");
    } else if (implementation.results && implementation.expected) {
      var caseResults = implementation.results.filter(
        (element) => element.skipped
      );
      if (caseResults.length > 0) {
        return (testResult = "skipped");
      }
      if (
        implementation.results.every(
          (each) => each.hasOwnProperty("errored") && typeof each === "object"
        )
      ) {
        return (testResult = "errored");
      }
      if (
        implementation.results.every(
          (element) =>
            typeof element === "object" &&
            Object.keys(element).length === 1 &&
            "valid" in element
        )
      ) {
        if (
          implementation.results[index].valid === implementation.expected[index]
        ) {
          if (implementation.expected[index] === true)
            return (testResult = "passed");
        }
      }
    } else if (implementation.results) {
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
                    var implementation = caseImplementation.find(
                      (each) => each.implementation === impl.image
                    );
                    {
                      /* console.log(index);
                    console.log(implementation);
                    console.log(i); */
                    }
                    var testResult = result(index, implementation);
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
                    } else if (testResult == "passed") {
                      return (
                        <td key={i} className="text-center">
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
                    } else {
                      return <td key={i}>Agni</td>;
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

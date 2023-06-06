import AccordionSvg from "./AccordionSvg";

const AccordionItem = ({ eachCase, implementations, caseImplementation }) => {
  const seq = eachCase.seq;
  const description = eachCase.case.description;
  const schema = eachCase.case.schema;
  const tests = eachCase.case.tests;

  function result(index, implementation) {
    var testResult;
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
          if (implementation.expected[index] === true) {
            return (testResult = "passed");
          } else {
            return (testResult = "failed");
          }
        } else if (
          implementation.results[index].valid !== implementation.expected[index]
        ) {
          if (implementation.expected[index] === false) {
            return (testResult = "unexpectedlyValid");
          } else {
            return (testResult = "unexpectedlyInvalid");
          }
        }
      }
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
                    var testResult = result(index, implementation);
                    return <AccordionSvg key={i} testResult={testResult} />;
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

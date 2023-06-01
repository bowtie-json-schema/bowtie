const AccordionItem = ({ eachCase, implementations, lines }) => {
  // console.log(implementations)
  const seq = eachCase.seq;
  const description = eachCase.case.description;
  const schema = eachCase.case.schema;
  const registry = eachCase.case.registry;
  const tests = eachCase.case.tests;

  const schemaDisplay = (id, schema, codeId, rowId) => {
    // Implementation for schemaDisplay function
  };

  const displayCode = (instance, infoId) => {
    // Implementation for displayCode function
  };

  const toIcon = (valid) => {
    // Implementation for toIcon function
  };

  return (
    <div className="accordion-item">
      <h2 className="accordion-header" id={`case-${seq}-heading`}>
        <button
          className="accordion-button collapsed"
          type="button"
          onClick={() =>
            schemaDisplay(
              `accordion-body${seq}`,
              JSON.stringify(schema, null, 2),
              "schema-code",
              `row-${seq}`
            )
          }
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
                    key={implementation.name+implementation.language}
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
                  onClick={() =>
                    displayCode(
                      JSON.stringify(testResult.instance, null, 2),
                      "instance-info"
                    )
                  }
                >
                  <td>
                    <a href="#schema" className="text-decoration-none">
                      {test.description}
                    </a>
                  </td>
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

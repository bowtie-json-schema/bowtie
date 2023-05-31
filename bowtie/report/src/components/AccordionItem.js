const AccordionItem = ({
  seq,
  description,
  schema,
  registry,
  results,
  implementations,
}) => {
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
                <td scope="col">Tests</td>
                {implementations.map((implementation) => (
                  <td
                    className="text-center"
                    scope="col"
                    key={implementation.name}
                  >
                    {implementation.name}
                    <small className="text-muted">
                      {implementation.language}
                    </small>
                  </td>
                ))}
              </tr>
            </thead>

            {results.map((testResult, index) => (
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
                    {testResult.test.description}
                  </a>
                </td>
                {implementations.map((implementation) => {
                  const [implementationResult, incorrect] =
                    testResult.test_results.get(implementation.image, {
                      valid: null,
                      incorrect: true,
                    });

                  if (incorrect === "skipped") {
                    return (
                      <td
                        className="text-center text-bg-warning"
                        key={implementation.name}
                      >
                        {toIcon(null)}
                      </td>
                    );
                  } else if (incorrect === "errored") {
                    return (
                      <td
                        className="text-center text-bg-danger"
                        key={implementation.name}
                      >
                        {toIcon(null)}
                      </td>
                    );
                  } else {
                    return (
                      <td
                        className={`text-center ${
                          incorrect
                            ? "text-bg-danger"
                            : implementationResult.valid !== true &&
                              implementationResult.valid !== false
                            ? "text-bg-warning"
                            : ""
                        }`}
                        key={implementation.name}
                      >
                        {toIcon(implementationResult.valid)}
                      </td>
                    );
                  }
                })}
              </tr>
            ))}
          </table>
        </div>
      </div>
    </div>
  );
};

export default AccordionItem;

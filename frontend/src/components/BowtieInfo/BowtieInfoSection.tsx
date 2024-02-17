const BowtieInfoSection = () => {
  return (
    <div className="card mx-auto mb-3 w-75" id="bowtie-info">
      <div className="card-header">About Bowtie</div>
      <div className="card-body">
        <table className="table table-sm table-hover">
          <thead>
            <tr>
              <td>
                Bowtie is tool for understanding and comparing implementations
                of the &nbsp;
                <a href={"https://json-schema.org/"}>
                  {"JSON Schema specification"}
                </a>
                &nbsp; across all programming languages. The report below uses
                the &nbsp;
                <a
                  href={
                    "https://github.com/json-schema-org/JSON-Schema-Test-Suite"
                  }
                >
                  {"official JSON Schema Test Suite"}
                </a>
                &nbsp; to display bugs or functionality gaps in implementations.
                You can also use Bowtie to get this information about your own
                schemas. You can find out how in its &nbsp;
                <a href={"https://docs.bowtie.report/"}>{"documentation"}</a>.
              </td>
            </tr>
          </thead>
        </table>
      </div>
    </div>
  );
};

export default BowtieInfoSection;

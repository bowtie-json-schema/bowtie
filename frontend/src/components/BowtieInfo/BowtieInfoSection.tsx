import Card from "react-bootstrap/Card";

const BowtieInfoSection = () => {
  // prettier-ignore
  return (
    <Card className="mx-auto mb-3" id="bowtie-info">
      <Card.Header>About Bowtie</Card.Header>
      <Card.Body>
        <p>
          Bowtie is tool for understanding and comparing implementations of the <a href={"https://json-schema.org/"}>{"JSON Schema specification"}</a> across all programming languages.
        </p>
        <p>
          The report below uses the <a href={"https://github.com/json-schema-org/JSON-Schema-Test-Suite"}>{"official JSON Schema Test Suite"}</a> to display bugs or functionality gaps in implementations.
        </p>
        <p>
          You can also use Bowtie to get this information about your own schemas.
          Find out how in <a href={"https://docs.bowtie.report/"}>{"Bowtie's documentation"}</a>.
        </p>
      </Card.Body>
    </Card>
  );
};

export default BowtieInfoSection;

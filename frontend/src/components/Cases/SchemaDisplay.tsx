import CopyToClipboard from "../CopyToClipboard";

const schemaStyle = {
  maxHeight: "30em",
};

const SchemaDisplay = ({
  schema,
  instance,
}: {
  instance: unknown;
  schema: Record<string, unknown> | boolean;
}) => {
  const schemaFormatted = JSON.stringify(schema, null, 2);
  const instanceFormatted = JSON.stringify(instance, null, 2);
  return (
    <div className="card mb-3 mw-100">
      <div className="d-flex">
        <div className="col-md-8 col-6 pe-0">
          <div className="d-flex align-items-center highlight-toolbar ps-3 pe-2 py-1 border-0 border-top border-bottom">
            <small className="font-monospace text-body-secondary text-uppercase">
              Schema
            </small>
            <div className="d-flex ms-auto">
              <CopyToClipboard textToCopy={schemaFormatted} />
            </div>
          </div>
          <div className="card-body">
            <pre id="schema-code" style={schemaStyle}>
              {schemaFormatted}
            </pre>
          </div>
        </div>
        <div className="col-md-4 col-6 border-start px-0">
          <div className="d-flex align-items-center highlight-toolbar ps-3 pe-2 py-1 border-0 border-top border-bottom">
            <small className="font-monospace text-body-secondary text-uppercase pe-4">
              Instance
            </small>
            <div className="d-flex ms-auto">
              <CopyToClipboard textToCopy={instanceFormatted} />
            </div>
          </div>
          <div id="instance-info" className="card-body">
            <pre id="schema-code" style={schemaStyle}>
              {instanceFormatted}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchemaDisplay;

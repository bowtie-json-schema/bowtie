import Table from "react-bootstrap/Table";

import { RunMetadata } from "../../data/parseReportData";

const RunInfoSection = ({ runMetadata }: { runMetadata: RunMetadata }) => {
  return (
    <div className="card mx-auto mb-3" id="run-info">
      <div className="card-header">Run Info</div>

      <div className="card-body table-responsive-sm">
        <Table size="sm" hover>
          <thead>
            <tr>
              <td className="align-top col-md-2">Dialect</td>
              <td>{runMetadata.dialect.uri}</td>
            </tr>
            <tr>
              <td className="align-top col-md-2">Ran</td>
              <td>{runMetadata.ago()}</td>
            </tr>
          </thead>
        </Table>

        {runMetadata.metadata && (
          <>
            <hr />
            <Table size="sm" id="run-metadata" hover>
              <thead>
                {Object.entries(runMetadata.metadata).map(([label, value]) => {
                  if (typeof value === "string") {
                    return (
                      <tr key={label}>
                        <td className="align-top col-md-2">{label}</td>
                        <td>{value}</td>
                      </tr>
                    );
                  } else if (
                    typeof value === "object" &&
                    value &&
                    "href" in value &&
                    typeof value.href === "string" &&
                    "text" in value &&
                    typeof value.text === "string"
                  ) {
                    return (
                      <tr key={label}>
                        <td className="align-top col-md-2">{label}</td>
                        <td>
                          <a href={value.href}>{value.text}</a>
                        </td>
                      </tr>
                    );
                  }
                  return null;
                })}
              </thead>
            </Table>
          </>
        )}
      </div>
    </div>
  );
};

export default RunInfoSection;

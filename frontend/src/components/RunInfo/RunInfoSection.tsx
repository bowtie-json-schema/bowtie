import moment from "moment";
import { RunInfo } from "../../data/parseReportData";
import "./RunInfoSection.css"
const RunInfoSection = ({ runInfo }: { runInfo: RunInfo }) => {
  const ranTime = (startTime: string) => {
    const currentTime = moment();
    const duration = moment.duration(currentTime.diff(startTime));
    return duration.humanize();
  };

  return (
    <div className="card mx-auto mb-3" id="run-info">
      <div className="card-header">Run Info</div>

      <div className="card-body table-responsive-sm">
        <table className="table table-sm table-hover">
          <thead>
            <tr>
              <td className="align-top col-md-2">Dialect</td>
              <td>{runInfo.dialect}</td>
            </tr>
            <tr>
              <td className="align-top col-md-2">Ran</td>
              <td>{ranTime(runInfo.started)} ago</td>
            </tr>
          </thead>
        </table>

        {runInfo.metadata && (
          <>
            <hr />
            <table id="run-metadata" className="table table-sm table-hover">
              <thead>
                {Object.entries(runInfo.metadata).map(([label, value]) => {
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
            </table>
          </>
        )}
      </div>
    </div>
  );
};

export default RunInfoSection;

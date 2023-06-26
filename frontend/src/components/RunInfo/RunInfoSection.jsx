import moment from "moment";

const RunInfoSection = (props) => {
  const ranTime = (startTime) => {
    const currentTime = moment();
    const duration = moment.duration(currentTime.diff(startTime));
    return duration.humanize();
  };

  return (
    <div className="card mx-auto mb-3 w-75" id="run-info">
      <div className="card-header">Run Info</div>

      <div className="card-body">
        <table className="table table-sm table-hover">
          <thead>
            <tr>
              <td>Dialect</td>
              <td>{props.runInfo.dialect}</td>
            </tr>
            <tr>
              <td>Ran</td>
              <td>{ranTime(props.runInfo.started)} ago</td>
            </tr>
          </thead>
        </table>

        {props.runInfo.metadata && (
          <>
            <hr />
            <table id="run-metadata" className="table table-sm table-hover">
              <thead>
                {Object.entries(props.runInfo.metadata).map(
                  ([label, value]) => {
                    if (typeof value === "string") {
                      return (
                        <tr key={label}>
                          <td>{label}</td>
                          <td>{value}</td>
                        </tr>
                      );
                    } else if (
                      typeof value === "object" &&
                      value.href &&
                      value.text
                    ) {
                      return (
                        <tr key={label}>
                          <td>{label}</td>
                          <td>
                            <a href={value.href}>{value.text}</a>
                          </td>
                        </tr>
                      );
                    }
                    return null;
                  },
                )}
              </thead>
            </table>
          </>
        )}
      </div>
    </div>
  );
};

export default RunInfoSection;

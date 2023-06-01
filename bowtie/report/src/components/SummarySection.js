import { RunInfo } from "../data/run-Info";
import SummaryTable from "./SummaryTable";


const SummarySection = (props) => {

  const lines = props.lines;
  const runInfo = new RunInfo(lines);
  const summary = runInfo.create_summary();
  // console.log(props.summary)
  return (
    <div className="card mx-auto mb-3 w-75" id="summary">
      <div className="card-header">Summary</div>
      <div className="card-body">
        <SummaryTable lines={lines} />
        {summary.did_fail_fast && (
          <div className="alert alert-warning" role="alert">
            This run failed fast, so some input cases may not have been run.
          </div>
        )}
      </div>
    </div>
  );
};

export default SummarySection;

import SummaryTable from "./SummaryTable";
import { ReportData } from "../../data/parseReportData.ts";

const SummarySection = ({ reportData }: { reportData: ReportData }) => {
  return (
    <div className="card mx-auto mb-3" id="summary">
      <div className="card-header">Summary</div>
      <div className="card-body">
        <SummaryTable reportData={reportData} />
        {reportData.didFailFast && (
          <div className="alert alert-warning" role="alert">
            This run failed fast, so some input cases may not have been run.
          </div>
        )}
      </div>
    </div>
  );
};

export default SummarySection;

import SummaryTable from "./SummaryTable";
import { Implementation, ReportData } from "../../data/parseReportData.ts";

const SummarySection = ({
  reportData,
  prevImplementations,
}: {
  reportData: ReportData;
  prevImplementations?: Record<string, Implementation> | null;
}) => {
  return (
    <div className="card mx-auto mb-3 w-75" id="summary">
      <div className="card-header">Summary</div>
      <div className="card-body">
        <SummaryTable
          reportData={reportData}
          prevImplementations={prevImplementations}
        />
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

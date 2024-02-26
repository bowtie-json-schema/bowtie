import SummaryTable from "./SummaryTable";
import { Implementation, ReportData } from "../../data/parseReportData.ts";
import { OtherImplementations } from "../OtherImplementations.tsx";

const SummarySection = ({
  reportData,
  otherImplementationsData,
}: {
  reportData: ReportData;
  otherImplementationsData: Record<string, Implementation>;
}) => {
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
        {Object.keys(otherImplementationsData).length > 0 && (
          <OtherImplementations
            otherImplementationsData={otherImplementationsData}
          />
        )}
      </div>
    </div>
  );
};

export default SummarySection;

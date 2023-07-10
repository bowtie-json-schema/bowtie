import CasesSection from "./components/Cases/CasesSection";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";

export const ReportView = ({ reportData }) => {
  return (
    <div>
      <div className="container p-4">
        <RunInfoSection runInfo={reportData.runInfo} />
        <SummarySection reportData={reportData} />
        <CasesSection reportData={reportData} />
      </div>
    </div>
  );
};

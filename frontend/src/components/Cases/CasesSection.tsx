import { ReportData } from "../../data/parseReportData";
import CaseItem from "./CaseItem";
import { Accordion } from "react-bootstrap";

const CasesSection = ({ reportData }: { reportData: ReportData }) => {
  const implementationsResults = Array.from(
    reportData.implementationsResults.values(),
  );
  const implementations = implementationsResults.map(
    (implResult) => reportData.runMetadata.implementations.get(implResult.id)!,
  );

  return (
    <Accordion id="cases">
      {Array.from(reportData.cases.entries()).map(([seq, caseData], index) => (
        <CaseItem
          key={index}
          seq={seq}
          caseData={caseData}
          implementations={implementations}
          implementationsResults={implementationsResults}
        />
      ))}
    </Accordion>
  );
};

export default CasesSection;

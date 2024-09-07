import Accordion from "react-bootstrap/Accordion";

import { ReportData } from "../../data/parseReportData";
import CaseItem from "./CaseItem";

const CasesSection = ({ reportData }: { reportData: ReportData }) => {
  const implementationsResults = Array.from(
    reportData.implementationsResults.values(),
  );
  const implementations = Array.from(
    reportData.implementationsResults.keys(),
  ).map((id) => reportData.runMetadata.implementations.get(id)!);

  return (
    <Accordion id="cases">
      {Array.from(reportData.cases.entries()).map(([seq, caseData]) => (
        <CaseItem
          key={seq.toString()}
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

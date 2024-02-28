import { ReportData } from "../../data/parseReportData";
import CaseItem from "./CaseItem";
import { Accordion } from "react-bootstrap";
import "./CasesSection.css";
const CasesSection = ({ reportData }: { reportData: ReportData }) => {
  const implementations = Array.from(reportData.implementations.values());
  return (
    <Accordion id="cases">
      {Array.from(reportData.cases.entries()).map(([seq, caseData], index) => (
        <CaseItem
          key={index}
          seq={seq}
          caseData={caseData}
          implementations={implementations}
        />
      ))}
    </Accordion>
  );
};

export default CasesSection;

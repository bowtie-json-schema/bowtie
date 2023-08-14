import CaseItem from "./CaseItem";
import { Accordion } from "react-bootstrap";

const CasesSection = ({ reportData }) => {
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

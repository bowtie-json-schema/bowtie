import AccordionItem from "./AccordionItem";
import {Accordion} from 'react-bootstrap'

const CasesSection = ({ reportData }) => {
  const implementations = Array.from(reportData.implementations.values());
  return (
    <Accordion>
      {Array.from(reportData.cases.entries()).map(([seq, caseData], index) => (
        <AccordionItem
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

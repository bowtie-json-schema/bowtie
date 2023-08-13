import AccordionItem from "./AccordionItem";
import { useLoaderData } from "react-router-dom";

const CasesSection = ({ reportData }) => {

  const loaderData = useLoaderData();
  if (!reportData) {
    reportData = loaderData;
  }
  const implementations = Array.from(reportData.implementations.values());
  return (
    <div className="accordion pt-5" id="cases">
      {Array.from(reportData.cases.entries()).map(([seq, caseData], index) => (
        <AccordionItem
          key={index}
          seq={seq}
          caseData={caseData}
          implementations={implementations}
        />
      ))}
    </div>
  );
};

export default CasesSection;

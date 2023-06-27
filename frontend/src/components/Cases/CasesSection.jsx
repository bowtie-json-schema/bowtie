import AccordionItem from "./AccordionItem";

const CasesSection = ({ reportData }) => {
  return (
    <div className="accordion pt-5" id="cases">
      {Array.from(reportData.cases.entries()).map(([seq, caseData], index) => (
          <AccordionItem
            key={index}
            seq={seq}
            caseData={caseData}
            implementations={Array.from(reportData.implementations.values())}
          />
        )
      )}
    </div>
  );
};

export default CasesSection;

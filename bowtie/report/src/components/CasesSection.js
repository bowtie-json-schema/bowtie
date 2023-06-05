import { RunInfo } from "../data/run-Info";
import AccordionItem from "./AccordionItem";

const CasesSection = ({ lines }) => {
  const CaseObjectArray = lines.filter((obj) => obj.case);
  const ImplementationObjectArray = lines.filter((obj) => obj.implementation);

  const runInfo = new RunInfo(lines);
  const summary = runInfo.create_summary();

  return (
    <div className="accordion pt-5" id="cases">
      {CaseObjectArray.map((eachCase, index) => {
        const caseImplementation = ImplementationObjectArray.filter(
          (implementation) => implementation.seq === eachCase.seq
        );
        return (
          <AccordionItem
            key={index}
            lines ={lines}
            implementations = {summary.implementations}
            eachCase={eachCase}
            caseImplementation={caseImplementation}
          />
        );
      })}
    </div>
  );
};

export default CasesSection;

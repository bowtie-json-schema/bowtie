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
        const ccaseImplementation = caseImplementation.find(
          (implementation) => implementation.implementation === summary.implementations[0].image
        );
        {/* console.log(ccaseImplementation)
        console.log(caseImplementation)
        console.log(summary.implementations) */}
        return (
          <AccordionItem
            key={index}
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

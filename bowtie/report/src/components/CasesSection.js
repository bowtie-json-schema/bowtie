import { RunInfo } from "../data/run-Info";
import AccordionItem from './AccordionItem';

const CasesSection = ({ lines }) => {
    const CaseObjectArray = lines.filter((obj) => obj.hasOwnProperty("case"));

  

    const runInfo = new RunInfo(lines);
    const summary = runInfo.create_summary()

  return (
    <div className="accordion pt-5" id="cases">
    {CaseObjectArray.map((eachCase, index) => (
      <AccordionItem key={index}  lines ={lines} eachCase={eachCase} implementations={summary.implementations} />
    ))}
    </div>
  );
};

export default CasesSection;

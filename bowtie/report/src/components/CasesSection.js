import AccordionItem from "./AccordionItem";

const CasesSection = ({ summary }) => {
    return (
      <div className="accordion pt-5" id="cases">
        {/* {summary.flat_results().map(([seq, description, schema, registry, results], index) => (
          <AccordionItem
             key={index}
             seq={seq}
             description={description}
             schema={schema}
             registry={registry}
             results={results}
             implementations={summary.implementations}
            />
        ))} */}
      </div>
    );
  };
  
  export default CasesSection;

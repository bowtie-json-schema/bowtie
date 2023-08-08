import AccordionSvg from "./AccordionSvg";
import SchemaDisplay from "./SchemaDisplay";
import {useEffect, useState, useTransition} from 'react'
import LoadingAnimation from '../LoadingAnimation'

const Content = ({ seq, caseData, implementations }) => {
  const [instance, setInstance] = useState();

  return (
  <div id={`accordion-body${seq}`} className="accordion-body">
    <SchemaDisplay schema={caseData.schema} instance={instance} />
    <table className="table table-hover">
      <thead>
      <tr>
        <td scope="col">
          <b>Tests</b>
        </td>
        {implementations.map((implementation) => (
          <td
            className="text-center"
            scope="col"
            key={
              implementation.metadata.name +
              implementation.metadata.language
            }
          >
            <b>{implementation.metadata.name + " "}</b>
            <small className="text-muted">
              {implementation.metadata.language}
            </small>
          </td>
        ))}
      </tr>
      </thead>
      <tbody>
      {caseData.tests.map((test, index) => (
        <tr key={index} onClick={() => setInstance(test.instance)}>
          <td>
            <p className="m-0">{test.description}</p>
          </td>
          {implementations.map((impl, i) => (
            <AccordionSvg key={i} result={impl.cases.get(seq)[index]} />
          ))}
        </tr>
      ))}
      </tbody>
    </table>
  </div>
)
}

const AccordionItem = ({ seq, caseData, implementations }) => {
  const [content, setContent] = useState(<LoadingAnimation/>);
  const [, startTransition] = useTransition();
  useEffect(() => {
    startTransition(() => setContent(<Content seq={seq} caseData={caseData} implementations={implementations}/> ))
  }, [seq, caseData, implementations])
  return (
    <div className="accordion-item">
      <h2 className="accordion-header" id={`case-${seq}-heading`}>
        <button
          className="accordion-button collapsed"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target={`#case-${seq}`}
          aria-expanded="false"
          aria-controls={`case-${seq}`}
        >
          <p className="m-0">{caseData.description}</p>
        </button>
      </h2>
      <div
        id={`case-${seq}`}
        className="accordion-collapse collapse"
        aria-labelledby={`case-${seq}-heading`}
        data-bs-parent="#cases"
      >
        {content}
      </div>
    </div>
  );
};

export default AccordionItem;

import CaseResultSvg from "./CaseResultSvg";
import SchemaDisplay from "./SchemaDisplay";
import {useEffect, useState, useTransition} from 'react'
import LoadingAnimation from '../LoadingAnimation'
import {Accordion} from 'react-bootstrap'

const CaseContent = ({ seq, caseData, implementations }) => {
  const [instance, setInstance] = useState();

  return (
  <>
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
            <CaseResultSvg key={i} result={impl.cases.get(seq)[index]} />
          ))}
        </tr>
      ))}
      </tbody>
    </table>
  </>
)
}

const CaseItem = ({ seq, caseData, implementations }) => {
  const [content, setContent] = useState(<LoadingAnimation/>);
  const [, startTransition] = useTransition();
  useEffect(() => {
    startTransition(() => setContent(<CaseContent seq={seq} caseData={caseData} implementations={implementations}/> ))
  }, [seq, caseData, implementations])
  return (
    <Accordion.Item eventKey={seq}>
      <Accordion.Header>
          {caseData.description}
      </Accordion.Header>
      <Accordion.Body>
        {content}
      </Accordion.Body>
    </Accordion.Item>
  );
};

export default CaseItem;

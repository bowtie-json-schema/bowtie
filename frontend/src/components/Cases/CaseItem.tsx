import CaseResultSvg from "./CaseResultSvg";
import SchemaDisplay from "./SchemaDisplay";
import { SetStateAction, useEffect, useState, useTransition } from "react";
import { Accordion } from "react-bootstrap";
import { mapLanguage } from "../../data/mapLanguage";
import {
  Case,
  CaseResult,
  ImplementationData,
} from "../../data/parseReportData";

interface CaseProps {
  seq: number;
  caseData: Case;
  implementations: ImplementationData[];
}

const CaseContent = ({ seq, caseData, implementations }: CaseProps) => {
  const [instance, setInstance] = useState<SetStateAction<unknown>>();

  return (
    <>
      <SchemaDisplay schema={caseData.schema} instance={instance} />
      <div className="overflow-x-auto">
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
                  <div className="flex-column d-flex">
                    <b>{implementation.metadata.name}</b>
                    <small className="text-muted">
                      {mapLanguage(implementation.metadata.language)}
                    </small>
                  </div>
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
                {implementations.map((impl, i) => {
                  const caseResults = impl.cases.get(seq);
                  const result: CaseResult =
                    caseResults !== undefined
                      ? caseResults[index]
                      : { state: "errored" };
                  return <CaseResultSvg key={i} result={result} />;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};

const CaseItem = ({ seq, caseData, implementations }: CaseProps) => {
  const [content, setContent] = useState(<></>);
  const [, startTransition] = useTransition();
  useEffect(() => {
    startTransition(() =>
      setContent(
        <CaseContent
          seq={seq}
          caseData={caseData}
          implementations={implementations}
        />,
      ),
    );
  }, [seq, caseData, implementations]);
  return (
    <Accordion.Item eventKey={seq.toString()}>
      <Accordion.Header>{caseData.description}</Accordion.Header>
      <Accordion.Body>{content}</Accordion.Body>
    </Accordion.Item>
  );
};

export default CaseItem;

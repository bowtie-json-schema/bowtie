import {
  SetStateAction,
  useEffect,
  useState,
  useTransition,
  useRef,
  RefObject,
} from "react";
import Accordion from "react-bootstrap/Accordion";

import CaseResultSvg from "./CaseResultSvg";
import SchemaDisplay from "./SchemaDisplay";
import Implementation from "../../data/Implementation";
import { mapLanguage } from "../../data/mapLanguage";
import {
  Case,
  CaseResult,
  ImplementationResults,
} from "../../data/parseReportData";

interface CaseProps {
  seq: number;
  caseData: Case;
  schemaDisplayRef?: RefObject<HTMLDivElement | null>;
  implementations: Implementation[];
  implementationsResults: ImplementationResults[];
}

const CaseContent = ({
  seq,
  schemaDisplayRef,
  caseData,
  implementations,
  implementationsResults,
}: CaseProps) => {
  const [instance, setInstance] = useState<SetStateAction<unknown>>(
    caseData.tests[0].instance,
  );
  const [activeRow, setActiveRow] = useState<SetStateAction<unknown>>(0);

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
                  key={implementation.name + implementation.language}
                >
                  <div className="flex-column d-flex">
                    <b>{implementation.name}</b>
                    <small className="text-muted">
                      {mapLanguage(implementation.language)}
                    </small>
                  </div>
                </td>
              ))}
            </tr>
          </thead>
          <tbody>
            {caseData.tests.map((test, index) => (
              <tr
                className={activeRow === index ? "table-active" : ""}
                key={index}
                onClick={() => {
                  setInstance(test.instance);
                  setActiveRow(index);
                  if (schemaDisplayRef) {
                    schemaDisplayRef.current?.scrollIntoView({
                      behavior: "smooth",
                      block: "start",
                    });
                  }
                }}
              >
                <td>
                  <p className="m-0">{test.description}</p>
                </td>
                {implementationsResults.map((implResult, i) => {
                  const caseResults = implResult.caseResults.get(seq);
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

const CaseItem = ({
  seq,
  caseData,
  implementations,
  implementationsResults,
}: CaseProps) => {
  const [content, setContent] = useState(<></>);
  const [, startTransition] = useTransition();
  const schemaDisplayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    startTransition(() =>
      setContent(
        <CaseContent
          seq={seq}
          caseData={caseData}
          implementations={implementations}
          implementationsResults={implementationsResults}
          schemaDisplayRef={schemaDisplayRef}
        />,
      ),
    );
  }, [seq, caseData, implementations, implementationsResults]);
  return (
    <Accordion.Item ref={schemaDisplayRef} eventKey={seq.toString()}>
      <Accordion.Header>{caseData.description}</Accordion.Header>
      <Accordion.Body>{content}</Accordion.Body>
    </Accordion.Item>
  );
};

export default CaseItem;

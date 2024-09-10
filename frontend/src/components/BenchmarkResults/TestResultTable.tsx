import { geometricMean, TestResult } from "../../data/parseBenchmarkData";
import { mean, std } from "mathjs";
import Table from "react-bootstrap/Table";
import { useEffect, useMemo, useRef, useState, useTransition } from "react";
import Accordion from "react-bootstrap/Accordion";
import OverlayTrigger from "react-bootstrap/OverlayTrigger";
import Tooltip from "react-bootstrap/Tooltip";

const TestResultTable = ({
  testResults,
  heading,
}: {
  testResults: TestResult[];
  heading: string;
}) => {
  function formatValue(value: number): string {
    if (value * 1000 < 1) {
      return `${Math.round(value * 1000 * 1000)}us`;
    } else if (value < 1) {
      return `${Math.round(value * 1000)}ms`;
    }
    return `${value.toFixed(2)}s`;
  }

  const sortedResultsForConnectable = useMemo(() => {
    const resultsForConnectable: Record<string, [number, number, boolean][]> =
      {};

    testResults[0].implementationResults.forEach(
      (implementationResult, idx) => {
        const implementationResults = testResults.map((testResult) => {
          const values = testResult.implementationResults[idx].values;
          return [
            mean(values), // Mean of the values
            std(values) as unknown, // Standard deviation of the values
            testResult.implementationResults[idx].errored, // Errored status
          ] as [number, number, boolean];
        });
        resultsForConnectable[implementationResult.implementationId] =
          implementationResults;
      },
    );

    const sortedConnectables = Object.entries(resultsForConnectable)
      .sort(
        ([, resultsA], [, resultsB]) =>
          Number(
            geometricMean(
              resultsA
                .filter(([, , errored]) => !errored)
                .map(([mean, ,]) => mean),
            ),
          ) -
          Number(
            geometricMean(
              resultsB
                .filter(([, , errored]) => !errored)
                .map(([mean, ,]) => mean),
            ),
          ),
      )
      .map(([key]) => key);

    return sortedConnectables.reduce(
      (acc, key) => {
        acc[key] = resultsForConnectable[key];
        return acc;
      },
      {} as Record<string, [number, number, boolean][]>,
    );
  }, [testResults]);

  const [content, setContent] = useState(<></>);
  const [, startTransition] = useTransition();
  const schemaDisplayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    startTransition(() =>
      setContent(
        <Table hover className="p-2">
          <thead>
            <tr>
              <th>Implementation</th>
              {testResults.map((testResult) => (
                <th key={testResult.description}>{testResult.description}</th>
              ))}
              <th>Geometric Mean of Time Taken</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(sortedResultsForConnectable).map(
              ([implementationId, testResults], index) =>
                testResults.filter(([, , errored]) => !errored).length > 0 && (
                  <OverlayTrigger
                    placement="right"
                    key={`overlay-${implementationId}`}
                    overlay={
                      <Tooltip
                        id="button-tooltip"
                        className={index != 0 ? "d-none" : ""}
                      >
                        Fastest Implementation
                      </Tooltip>
                    }
                  >
                    <tr
                      key={implementationId}
                      className={index == 0 ? "table-success" : ""}
                    >
                      <td>{implementationId}</td>
                      {testResults.map(([mean_value, std_dev, errored]) => (
                        <td
                          key={mean_value}
                          className={errored ? "table-danger" : ""}
                        >
                          {errored
                            ? "Errored"
                            : `${formatValue(mean_value)} ± ${formatValue(
                                std_dev,
                              )}`}
                        </td>
                      ))}
                      <td>
                        {formatValue(
                          geometricMean(
                            testResults
                              .filter(([, , errored]) => !errored)
                              .map(([mean]) => mean),
                          ),
                        )}
                      </td>
                    </tr>
                  </OverlayTrigger>
                ),
            )}
          </tbody>
        </Table>,
      ),
    );
  }, [testResults, sortedResultsForConnectable]);

  return (
    <Accordion.Item ref={schemaDisplayRef} eventKey={heading}>
      <Accordion.Header>
        <div className="container-fluid">
          <div className="row">
            <div className="col-12 fw-bold mb-2">{heading}</div>
          </div>
        </div>
      </Accordion.Header>
      <Accordion.Body>{content}</Accordion.Body>
    </Accordion.Item>
  );
};

export default TestResultTable;

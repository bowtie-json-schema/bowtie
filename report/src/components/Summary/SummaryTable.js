import { CountsDataContext } from "../../data/CountsDataContext";
import { RunInfo } from "../../data/run-Info";
import ImplementationRow from "./ImplementationRow";
import { useContext } from "react";

const SummaryTable = ({ lines }) => {
  const runInfo = new RunInfo(lines);
  const summary = runInfo.createSummary();

  const caseArray = lines.filter((each) => each.case);
  const totalCases = caseArray.length;
  const totalTests = caseArray.reduce((total, eachCase) => {
    const caseTests = eachCase.case.tests;
    const caseTestCount = caseTests.length;
    return total + caseTestCount;
  }, 0);

  const {
    updateTotalErroredCases,
    updateTotalErroredTests,
    updateTotalFailedTests,
    updateTotalSkippedTests,
  } = useContext(CountsDataContext);

  // updateTotalErroredCases(10)

  const {
    totalErroredCases,
    totalErroredTests,
    totalFailedTests,
    totalSkippedTests,
  } = useContext(CountsDataContext);

  return (
    <table className="table table-sm table-hover">
      <thead>
        <tr>
          <th
            colSpan={2}
            rowSpan={2}
            scope="col"
            className="text-center align-middle"
          >
            implementation
          </th>
          <th colSpan={1} className="text-center">
            <span className="text-muted">cases ({totalCases})</span>
          </th>
          <th colSpan={3} className="text-center">
            <span className="text-muted">tests ({totalTests})</span>
          </th>
          <th colSpan={1}></th>
        </tr>
        <tr>
          <th scope="col" className="text-center">
            errors
          </th>
          <th scope="col" className="table-bordered text-center">
            skipped
          </th>
          <th
            scope="col"
            className="table-bordered text-center details-required"
          >
            <div className="hover-details details-desc text-center">
              <p>
                failed
                <br />
                <span>
                  implementation worked successfully but got the wrong answer
                </span>
              </p>
              <p>
                errored
                <br />
                <span>
                  implementation crashed when trying to calculate an answer
                </span>
              </p>
            </div>
            unsuccessful
          </th>
          <th scope="col"></th>
        </tr>
      </thead>
      <tbody className="table-group-divider">
        {summary.implementations.map((implementation, index) => (
          <ImplementationRow
            lines={lines}
            implementation={implementation}
            key={index}
            index={index}
          />
        ))}
      </tbody>
      <tfoot>
        <tr>
          <th scope="row" colSpan={2}>
            total
          </th>
          <td className="text-center">{totalErroredCases}</td>
          <td className="text-center">{totalSkippedTests}</td>
          <td className="text-center details-required">
            {totalFailedTests + totalErroredTests}
            <div className="hover-details text-center">
              <p>
                <b>failed</b>: {summary.failed_tests}
              </p>
              <p>
                <b>errored</b>: {summary.errored_tests}
              </p>
            </div>
          </td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  );
};

export default SummaryTable;

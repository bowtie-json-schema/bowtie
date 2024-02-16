import ImplementationRow from "./ImplementationRow";
import { useMemo } from "react";
import { ReportData, calculateTotals } from "../../data/parseReportData";

const SummaryTable = ({ reportData }: { reportData: ReportData }) => {
  const totals = useMemo(() => calculateTotals(reportData), [reportData]);
  return (
    <table className="table table-hover">
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
            <span className="text-muted">cases ({reportData.cases.size})</span>
          </th>
          <th colSpan={3} className="text-center">
            <span className="text-muted">tests ({totals.totalTests})</span>
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
        {Array.from(reportData.implementations.values())
          .sort(
            (a, b) =>
              a.failedTests +
              a.erroredTests +
              a.skippedTests -
              b.failedTests -
              b.erroredTests -
              b.skippedTests,
          )
          .map((implementation, index) => (
            <ImplementationRow
              cases={reportData.cases}
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
          <td className="text-center">{totals.erroredCases}</td>
          <td className="text-center">{totals.skippedTests}</td>
          <td className="text-center details-required">
            {totals.failedTests + totals.erroredTests}
            <div className="hover-details text-center">
              <p>
                <b>failed</b>: {totals.failedTests}
              </p>
              <p>
                <b>errored</b>: {totals.erroredTests}
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

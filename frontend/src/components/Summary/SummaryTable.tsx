import { useMemo } from "react";
import Table from "react-bootstrap/Table";
import StatusLegend from "./StatusLegend";
import ImplementationRow from "./ImplementationRow";
import { ReportData, calculateTotals } from "../../data/parseReportData";

const SummaryTable = ({ reportData }: { reportData: ReportData }) => {
  const totals = useMemo(() => calculateTotals(reportData), [reportData]);
  return (
    <Table hover responsive>
      <thead>
        <tr>
          <th
            scope="col"
            colSpan={2}
            rowSpan={2}
            className="text-center align-middle"
          >
            implementation
          </th>
          <th scope="col" colSpan={2} className="text-center">
            <span className="text-muted">cases ({reportData.cases.size})</span>
          </th>
          <th scope="col" colSpan={2} className="text-center">
            <span className="text-muted">tests ({totals.totalTests})</span>
          </th>
        </tr>
        <tr>
          <StatusLegend>
            <th
              scope="col"
              colSpan={4}
              className="table-bordered text-center details-required"
            >
              unsuccessful
            </th>
          </StatusLegend>
        </tr>
      </thead>
      <tbody className="table-group-divider">
        {Array.from(reportData.implementationsResults.entries())
          .sort(
            ([, a], [, b]) =>
              a.totals.failedTests! +
              a.totals.erroredTests! +
              a.totals.skippedTests! -
              b.totals.failedTests! -
              b.totals.erroredTests! -
              b.totals.skippedTests!,
          )
          .map(([id, implResults]) => (
            <ImplementationRow
              key={id}
              cases={reportData.cases}
              implementation={reportData.runMetadata.implementations.get(id)!}
              implementationResults={implResults}
            />
          ))}
      </tbody>
    </Table>
  );
};

export default SummaryTable;

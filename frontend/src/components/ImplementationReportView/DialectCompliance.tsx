import React from "react";
import { Card, Table } from "react-bootstrap";
import { Implementation } from "../../data/parseReportData";
import Dialect from "../../data/Dialect";
import { complianceBadgeFor } from "../../data/Badge";

const DialectCompliance: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  return (
    <Card className="mx-auto mb-3 col-md-9">
      <Card.Header>Compliance</Card.Header>
      <Card.Body>
        <Table className="table-hover sm">
          <thead>
            <tr>
              <th rowSpan={2} scope="col" className="text-center align-middle">
                Supported Dialects
              </th>
              <th colSpan={3} className="text-center">
                Tests
              </th>
              <th rowSpan={2} scope="col" className="text-center align-middle">
                Badge
              </th>
            </tr>
            <tr className="text-center">
              <th>Failed</th>
              <th>Skipped</th>
              <th>Errored</th>
            </tr>
          </thead>
          <tbody className="table-group-divider">
            {Object.entries(implementation.results)
              .sort(
                (a, b) =>
                  a[1].failedTests! +
                    a[1].erroredTests! +
                    a[1].skippedTests! -
                    b[1].failedTests! -
                    b[1].erroredTests! -
                    b[1].skippedTests! ||
                  +Dialect.forPath(b[0]).firstPublicationDate -
                    +Dialect.forPath(a[0]).firstPublicationDate,
              )
              .map(([dialectName, result], index) => {
                const dialect = Dialect.forPath(dialectName);
                return (
                  <tr key={index}>
                    <td>{dialect.prettyName}</td>
                    <td className="text-center">{result.failedTests}</td>
                    <td className="text-center">{result.skippedTests}</td>
                    <td className="text-center">{result.erroredTests}</td>
                    <td>
                      <a
                        className="mx-1"
                        // FIXME: surely this shouldn't be hardcoded
                        // Double FIXME: This should go to the
                        // implementation-specific page, not the global dialect
                        // one.
                        href={`/dialects/${dialect.path}`}
                        target="_blank"
                      >
                        <img
                          alt={dialect.prettyName}
                          className="float-end"
                          src={complianceBadgeFor(
                            implementation,
                            dialect,
                          ).href()}
                        />
                      </a>
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default DialectCompliance;

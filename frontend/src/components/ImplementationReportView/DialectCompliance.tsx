import React from "react";
import { Link } from "react-router-dom";
import Card from "react-bootstrap/Card";
import Image from "react-bootstrap/Image";
import Table from "react-bootstrap/Table";

import { complianceBadgeFor } from "../../data/Badge";
import { ImplementationReport } from "../../data/parseReportData";

const DialectCompliance: React.FC<{
  implementationReport: ImplementationReport;
}> = ({ implementationReport }) => {
  const { implementation, dialectCompliance } = implementationReport;

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
            {Array.from(dialectCompliance.entries())
              .sort(
                (a, b) =>
                  a[1].failedTests! +
                    a[1].erroredTests! +
                    a[1].skippedTests! -
                    b[1].failedTests! -
                    b[1].erroredTests! -
                    b[1].skippedTests! ||
                  +b[0].firstPublicationDate - +a[0].firstPublicationDate,
              )
              .map(([dialect, result], index) => {
                return (
                  <tr key={index}>
                    <td>{dialect.prettyName}</td>
                    <td className="text-center">{result.failedTests}</td>
                    <td className="text-center">{result.skippedTests}</td>
                    <td className="text-center">{result.erroredTests}</td>
                    <td>
                      <Link className="mx-1" to={dialect.routePath}>
                        <Image
                          src={complianceBadgeFor(
                            implementation,
                            dialect,
                          ).href()}
                          alt={dialect.prettyName}
                          className="float-end"
                        />
                      </Link>
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

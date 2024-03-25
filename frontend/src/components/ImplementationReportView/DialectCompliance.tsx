import React from "react";
import { Link } from "react-router-dom";
import Card from "react-bootstrap/Card";
import Image from "react-bootstrap/Image";
import Table from "react-bootstrap/Table";

import { complianceBadgeFor } from "../../data/Badge";
import Dialect from "../../data/Dialect";
import { ImplementationDialectCompliance } from "../../data/parseReportData";

const DialectCompliance: React.FC<{
  implementationDialectCompliance: ImplementationDialectCompliance;
}> = ({ implementationDialectCompliance }) => {
  const { implementation, dialectCompliance } = implementationDialectCompliance;

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
            {Object.entries(dialectCompliance)
              .sort(
                (a, b) =>
                  a[1].failedTests! +
                    a[1].erroredTests! +
                    a[1].skippedTests! -
                    b[1].failedTests! -
                    b[1].erroredTests! -
                    b[1].skippedTests! ||
                  +Dialect.withName(b[0]).firstPublicationDate -
                    +Dialect.withName(a[0]).firstPublicationDate,
              )
              .map(([dialectName, result], index) => {
                const dialect = Dialect.withName(dialectName);
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

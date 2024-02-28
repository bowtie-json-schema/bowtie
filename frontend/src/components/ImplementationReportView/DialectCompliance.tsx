import React from "react";
import { Card, Table } from "react-bootstrap";
import { Implementation } from "../../data/parseReportData";
import Dialect from "../../data/Dialect";
import { reportUri } from "../../data/ReportHost";
import { Link } from "react-router-dom";

const DialectCompliance: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  const reportURIpath: string = reportUri.href();

  const complianceBadgeURI = (dialectName: string): string => {
    return `https://img.shields.io/endpoint?url=${encodeURIComponent(
      `${reportURIpath}badges/${implementation.language}-${
        implementation.name
      }/compliance/${Dialect.forPath(dialectName).path}.json`
    )}`;
  };

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
                    +Dialect.forPath(a[0]).firstPublicationDate
              )
              .map(([dialectName, result], index) => {
                return (
                  <tr key={index}>
                    <td>
                      {Dialect.forPath(dialectName).uri}
                      <Link
                        className="mx-1"
                        to={Dialect.forPath(dialectName).uri}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: "inline-block",
                          width: "fit-content",
                        }}
                      >
                        <img
                          alt={`${Dialect.forPath(dialectName).prettyName}`}
                          src={complianceBadgeURI(dialectName)}
                        />
                      </Link>
                    </td>
                    <td className="text-center">{result.failedTests}</td>
                    <td className="text-center">{result.skippedTests}</td>
                    <td className="text-center">{result.erroredTests}</td>
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

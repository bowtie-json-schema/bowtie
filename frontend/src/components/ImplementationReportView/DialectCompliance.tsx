import React from "react";
import { Card, Table } from "react-bootstrap";
import { Implementation } from "../../data/parseReportData";
import Dialect from "../../data/Dialect";

const DialectCompliance: React.FC<{
  implementation: Implementation;
}> = ({ implementation }) => {
  return (
    <Card className="mx-auto mb-3 w-75">
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
                      {Dialect.forPath(dialectName).uri}{" "}
                      <img
                        width={140}
                        height={20}
                        src={`https://img.shields.io/endpoint?url=https%3A%2F%2Fbowtie-json-schema.github.io%2Fbowtie%2Fbadges%2F${encodeURIComponent(
                          implementation.language
                        )}-${implementation.name}%2Fcompliance%2FDraft_${
                          Dialect.forPath(dialectName).prettyName.split(" ")[1]
                        }.json`}
                      ></img>
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

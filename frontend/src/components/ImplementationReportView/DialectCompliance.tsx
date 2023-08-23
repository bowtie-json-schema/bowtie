import React from "react";
import { Card, Table } from "react-bootstrap";
import { ImplementationMetadata } from "../../data/parseReportData";
import { Dialect } from "../../data/Dialect";

const DialectCompliance: React.FC<{ specificData: ImplementationMetadata }> = ({
  specificData,
}) => {
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
            {Object.entries(specificData.results).map(
              ([draft, result], index) => {
                return (
                  <tr key={index}>
                    <td>{Dialect.dialectMapping[draft]}</td>
                    <td className="text-center">{result.unsuccessfulTests}</td>
                    <td className="text-center">{result.skippedTests}</td>
                    <td className="text-center">{result.erroredTests}</td>
                  </tr>
                );
              },
            )}
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default DialectCompliance;

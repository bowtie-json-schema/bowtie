import React from "react";
import { Card, Table } from "react-bootstrap";
import { ImplementationMetadata } from "../../data/parseReportData";

const DialectCompliance: React.FC<{ specificData: ImplementationMetadata }> = ({
  specificData,
}) => {
  const dialectMapping: { [key: string]: string } = {
    "draft2020-12": "https://json-schema.org/draft/2020-12",
    "draft2019-09": "https://json-schema.org/draft/2019-09",
    draft7: "http://json-schema.org/draft-07",
    draft6: "http://json-schema.org/draft-06",
    draft4: "http://json-schema.org/draft-04",
    draft3: "http://json-schema.org/draft-03",
  };

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
              <th>Unsuccessful</th>
              <th>Skipped</th>
              <th>Errored</th>
            </tr>
          </thead>
          <tbody className="table-group-divider">
            {Object.entries(specificData.results).map(
              ([draft, result], index) => {
                return (
                  <tr key={index}>
                    <td>{dialectMapping[draft]}</td>
                    <td className="text-center">{result.unsuccessfulTests}</td>
                    <td className="text-center">{result.skippedTests}</td>
                    <td className="text-center">{result.erroredTests}</td>
                  </tr>
                );
              }
            )}
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default DialectCompliance;

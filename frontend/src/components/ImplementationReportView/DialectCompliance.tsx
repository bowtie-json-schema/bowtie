import React from "react";
import { Card, Table } from "react-bootstrap";
import { ReportData } from "../../data/parseReportData";

interface DialectComplianceProps {
    loaderData: { [key: string]: ReportData };
    implementationsDetail: {
        dialects: string[];
        homepage: string;
        name: string;
    };
    implementationName: string;
}

const DialectCompliance: React.FC<DialectComplianceProps> = ({ loaderData, implementationsDetail, implementationName }) => {

    const dialectMapping = {
        "https://json-schema.org/draft/2020-12": "draft2020-12",
        "https://json-schema.org/draft/2019-09": "draft2019-09",
        "http://json-schema.org/draft-07": "draft7",
        "http://json-schema.org/draft-06": "draft6",
        "http://json-schema.org/draft-04": "draft4",
        "http://json-schema.org/draft-03": "draft3"
    };

    return (
        <Card className="mx-auto mb-3 w-75">
            <Card.Header>Compliance</Card.Header>
            <Card.Body>
                <Table className="table-hover sm">
                    <thead>
                        <tr>
                            <th
                                rowSpan={2}
                                scope="col"
                                className="text-center align-middle"
                            >
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

                        {implementationsDetail.dialects.map((dialect, index) => {
                            const draft = Object.entries(dialectMapping).find(([key,]) => dialect.includes(key));
                            if (draft && loaderData[draft[1]] && loaderData[draft[1]].implementations) {
                                const specificDialect = Array.from(loaderData[draft[1]].implementations).find(([key, value]) => key.includes(implementationName));
                                if (specificDialect) {
                                    return (
                                        <tr key={index}>
                                            <td>{dialect}</td>
                                            <td className="text-center">{specificDialect[1].unsuccessfulTests}</td>
                                            <td className="text-center">{specificDialect[1].skippedTests}</td>
                                            <td className="text-center">{specificDialect[1].erroredTests}</td>
                                        </tr>
                                    );
                                }
                            }
                            return null;
                        })}
                    </tbody>
                </Table>
            </Card.Body>
        </Card>
    );
};

export default DialectCompliance;

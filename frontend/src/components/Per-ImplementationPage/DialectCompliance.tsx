import React from "react";
import { Card, Table } from "react-bootstrap";
import { ReportData } from "../../data/parseReportData";

interface DialectComplianceProps {
    loaderData: ReportData;
    implementationsDetail: {
        [x: string]: any;
    }
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
                <Table striped bordered size="sm">
                    <thead>
                        <tr className="text-center">
                            <th>Dialects</th>
                            <th>Unsuccessful</th>
                            <th>Skipped</th>
                            <th>Errored</th>
                        </tr>
                        {implementationsDetail.dialects.map((dialect: string, index: number) => {
                            const draft = Object.entries(dialectMapping).find(([key,]) => dialect.includes(key));
                            if (draft && loaderData[draft[1]] && loaderData[draft[1]].implementations) {
                                const specificDialect = Array.from(loaderData[draft[1]].implementations).find(([key, value]) => key.includes(implementationName));
                                if (specificDialect) {
                                    return (
                                        <tr key={index}>
                                            <td>{dialect}</td>
                                            <td>{specificDialect[1].unsuccessfulTests}</td>
                                            <td>{specificDialect[1].skippedTests}</td>
                                            <td>{specificDialect[1].erroredTests}</td>
                                        </tr>
                                    );
                                }
                            }
                            return null;
                        })}
                    </thead>
                </Table>
            </Card.Body>
        </Card>
    );
};

export default DialectCompliance;

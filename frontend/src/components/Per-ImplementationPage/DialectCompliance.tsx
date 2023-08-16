import React from "react";
import { Card, Table } from "react-bootstrap";
import { fetchReportData } from "../../index";

interface DialectComplianceProps {
    dialects: string[];
}

const DialectCompliance: React.FC<DialectComplianceProps> = ({ dialects }) => {
    return (
        <Card className="mx-auto mb-3 w-75">
            <Card.Header>Compliance</Card.Header>
            <Card.Body>
                <Table striped bordered size="sm">
                    <thead>
                        <tr className="text-center">
                            <th>Dialects</th>
                            <th>Failed</th>
                            <th>Skipped</th>
                            <th>Errored</th>
                        </tr>
                        {dialects.map((dialect, index) => (
                            <tr key={index}>
                                <td>{dialect}</td>
                                <td></td>
                                <td></td>
                                <td></td>
                            </tr>
                        ))}

                    </thead>
                </Table>
            </Card.Body>
        </Card>
    );
};

export default DialectCompliance;

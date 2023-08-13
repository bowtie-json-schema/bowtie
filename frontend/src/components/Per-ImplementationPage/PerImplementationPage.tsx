import { Card } from "react-bootstrap";
import { useLoaderData } from "react-router-dom";
import { Table, Container } from 'react-bootstrap';

export const PerImplementationPage = () => {
    const loaderData = useLoaderData();
    console.log((loaderData.runInfo));
    console.log((loaderData.runInfo.dialect));
    return (
        <Container className="p-4">
            {/* {Object.entries(loaderData).forEach(([key, value]) => {
                console.log(`${key}: ${value}`);
            })} */}
            <Card className="mx-auto mb-3 w-75">
                <Card.Header>Runtime Info</Card.Header>
                <Card.Body>
                    <Table striped bordered size="sm">
                        <tbody>
                            <tr>
                                <th>1</th>
                                <td>Mark</td>
                            </tr>
                            <tr>
                                <th>2</th>
                                <td>Jacob</td>
                            </tr>
                            <tr>
                                <th>3</th>
                                <td>twitter</td>
                            </tr>
                        </tbody>
                    </Table>
                </Card.Body>
            </Card>
        </Container>
    );
}

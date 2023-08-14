import { Card } from "react-bootstrap";
import { useLoaderData, Link } from "react-router-dom";
import { Table, Container } from "react-bootstrap";
import { ReportData, ImplementationMetadata } from "../../data/parseReportData";
// @ts-ignore
import LoadingAnimation from "../../components/LoadingAnimation";

export const PerImplementationPage = () => {
  const loaderData = useLoaderData() as ReportData;

  const pathSegments = window.location.href.split("/");
  let implementationName = pathSegments[pathSegments.length - 1];

  let implementationDetails: ImplementationMetadata = {};
  Object.keys(loaderData.runInfo.implementations).forEach((key) => {
    if (key.includes(implementationName)) {
      implementationDetails = loaderData.runInfo.implementations[key];
    }
  });
  return implementationDetails ? (
    <Container className="p-4">
      <Card className="mx-auto mb-3 w-75">
        <Card.Header>Runtime Info</Card.Header>
        <Card.Body>
          <Table striped bordered size="sm">
            <tbody>
              <tr>
                <th>Name</th>
                <td>{implementationDetails.name}</td>
              </tr>
              <tr>
                <th>Language</th>
                <td>
                  {implementationDetails.language}
                  <span className="text-muted">{` (${implementationDetails.version})`}</span>
                </td>
              </tr>
              <tr>
                <th>Dialects</th>
                <td>
                  <ul>
                    {implementationDetails.dialects.map((dialect, index) => (
                      <li key={index}>
                        <Link to={dialect}>{dialect}</Link>
                      </li>
                    ))}
                  </ul>
                </td>
              </tr>
              <tr>
                <th>Image</th>
                <td>
                  <Link to={implementationDetails.image}>
                    {implementationDetails.image}
                  </Link>
                </td>
              </tr>
              <tr>
                <th>Homepage</th>
                <td>
                  <Link to={implementationDetails.homepage}>
                    {implementationDetails.homepage}
                  </Link>
                </td>
              </tr>
              <tr>
                <th>Issues</th>
                <td>
                  <Link to={implementationDetails.issues}>
                    {implementationDetails.issues}
                  </Link>
                </td>
              </tr>
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </Container>
  ) : (
    <LoadingAnimation />
  );
};

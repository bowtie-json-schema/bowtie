import { Card } from "react-bootstrap";
import { useLoaderData, Link } from "react-router-dom";
import { Table, Container } from "react-bootstrap";
import { ReportData, ImplementationMetadata } from "../../data/parseReportData";
// @ts-ignore
import LoadingAnimation from "../LoadingAnimation";
import DialectCompliance from "./DialectCompliance";
import { mapLanguage } from "../../data/mapLanguage";

export const ImplementationReportView = () => {
  const loaderData = useLoaderData() as { [key: string]: ReportData };

  const pathSegments = window.location.href.split("/");
  let implementationName = pathSegments[pathSegments.length - 1];

  let implementationDetail: ImplementationMetadata = {
    dialects: [],
    homepage: "",
    name: "",
    version: "",
    language: "",
    issues: "",
    image: "",
  };

  let allImplementations: { [key: string]: ImplementationMetadata } = {};
  Object.values(loaderData).map((value) => {
    allImplementations = {
      ...allImplementations,
      ...value.runInfo.implementations,
    };
  });
  Object.keys(allImplementations).forEach((key) => {
    if (key.includes(implementationName)) {
      implementationDetail = allImplementations[key];
      document.title = `Bowtie - ${implementationDetail.name}`;
    }
  });

  const ReportComponent = () => {
    return (
      <Container className="p-4">
        <Card className="mx-auto mb-3 w-75">
          <Card.Header>Runtime Info</Card.Header>
          <Card.Body>
            <Table>
              <tbody>
                <tr>
                  <th>Name:</th>
                  <td>{implementationDetail.name}</td>
                </tr>
                <tr>
                  <th>Version:</th>
                  <td>{implementationDetail.version}</td>
                </tr>
                <tr>
                  <th>Language:</th>
                  <td>
                    {mapLanguage(implementationDetail.language)}
                    <span className="text-muted">
                      {implementationDetail.language &&
                        ` (${implementationDetail.language_version || ""})`}
                    </span>
                  </td>
                </tr>
                <tr>
                  <th>OS:</th>
                  <td>
                    {implementationDetail.os || ""}
                    <span className="text-muted">
                      {implementationDetail.os &&
                        ` (${implementationDetail.os_version})`}
                    </span>
                  </td>
                </tr>
                <tr>
                  <th>Dialects:</th>
                  <td>
                    <ul>
                      {implementationDetail.dialects.map((dialect, index) => (
                        <li key={index}>
                          <Link to={dialect}>{dialect}</Link>
                        </li>
                      ))}
                    </ul>
                  </td>
                </tr>
                <tr>
                  <th>Image:</th>
                  <td>
                    <Link to={implementationDetail.image}>
                      {implementationDetail.image}
                    </Link>
                  </td>
                </tr>
                <tr>
                  <th>Homepage:</th>
                  <td>
                    <Link to={implementationDetail.homepage}>
                      {implementationDetail.homepage}
                    </Link>
                  </td>
                </tr>
                <tr>
                  <th>Issues:</th>
                  <td>
                    <Link to={implementationDetail.issues}>
                      {implementationDetail.issues}
                    </Link>
                  </td>
                </tr>
              </tbody>
            </Table>
          </Card.Body>
        </Card>
        <DialectCompliance
          loaderData={loaderData}
          implementationsDetail={implementationDetail}
          implementationName={implementationName}
        />
      </Container>
    );
  };

  return implementationDetail ? <ReportComponent /> : <LoadingAnimation />;
};

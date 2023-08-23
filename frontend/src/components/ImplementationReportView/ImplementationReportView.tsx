import { Card } from "react-bootstrap";
import { useLoaderData, useParams, Link } from "react-router-dom";
import { Table, Container } from "react-bootstrap";
import { ImplementationMetadata } from "../../data/parseReportData";
// @ts-ignore
import LoadingAnimation from "../LoadingAnimation";
import DialectCompliance from "./DialectCompliance";
import { mapLanguage } from "../../data/mapLanguage";

export const ImplementationReportView = () => {
  const allImplementations = useLoaderData() as {
    [key: string]: ImplementationMetadata;
  };

  const { langImplementation } = useParams();
  const implementationName = langImplementation ?? "";

  function filterImplementation(
    object: { [key: string]: ImplementationMetadata },
    implementationName: string
  ): ImplementationMetadata {
    const filteredKeys = Object.keys(object).filter((key) =>
      key.includes(implementationName)
    );
    return object[filteredKeys[0]];
  }

  const specificData = filterImplementation(
    allImplementations,
    implementationName
  );

  return allImplementations ? (
    <ReportComponent specificData={specificData} />
  ) : (
    <LoadingAnimation />
  );
};

const ReportComponent: React.FC<{ specificData: ImplementationMetadata }> = ({
  specificData,
}) => {
  return (
    <Container className="p-4">
      <Card className="mx-auto mb-3 w-75">
        <Card.Header>Implementation Info</Card.Header>
        <Card.Body>
          <Table>
            <tbody>
              <tr>
                <th>Name:</th>
                <td>{specificData.name}</td>
              </tr>
              <tr>
                <th>Version:</th>
                <td>{specificData.version}</td>
              </tr>
              <tr>
                <th>Language:</th>
                <td>
                  {mapLanguage(specificData.language)}
                  <span className="text-muted">
                    {specificData.language &&
                      specificData.language_version &&
                      ` (${specificData.language_version || ""})`}
                  </span>
                </td>
              </tr>
              <tr>
                <th>OS:</th>
                <td>
                  {specificData.os || ""}
                  <span className="text-muted">
                    {specificData.os &&
                      specificData.os_version &&
                      ` (${specificData.os_version})`}
                  </span>
                </td>
              </tr>
              <tr>
                <th>Dialects:</th>
                <td>
                  <ul>
                    {specificData.dialects.map(
                      (dialect: string, index: number) => (
                        <li key={index}>
                          <Link to={dialect}>{dialect}</Link>
                        </li>
                      )
                    )}
                  </ul>
                </td>
              </tr>
              <tr>
                <th>Image:</th>
                <td>{specificData.image}</td>
              </tr>
              <tr>
                <th>Homepage:</th>
                {specificData.homepage && (
                  <td>
                    <Link to={specificData.homepage}>
                      {specificData.homepage}
                    </Link>
                  </td>
                )}
              </tr>
              <tr>
                <th>Issues:</th>
                <td>
                  <Link to={specificData.issues}>{specificData.issues}</Link>
                </td>
              </tr>
            </tbody>
          </Table>
        </Card.Body>
      </Card>
      <DialectCompliance specificData={specificData} />
    </Container>
  );
};

import { Card } from "react-bootstrap";
import { useLoaderData, useParams, Link } from "react-router-dom";
import { Table, Container } from "react-bootstrap";
import { ImplementationMetadata } from "../../data/parseReportData";
// @ts-ignore
import LoadingAnimation from "../LoadingAnimation";
import DialectCompliance from "./DialectCompliance";
import { mapLanguage } from "../../data/mapLanguage";

export const ImplementationReportView = () => {
  // Fetch all supported implementation's metadata.
  const allImplementations = useLoaderData() as {
    [key: string]: ImplementationMetadata;
  };

  // Get the selected implementation's name from the URL parameters.
  const { langImplementation } = useParams();
  const implementationName = langImplementation ?? "";


  function getFilteredImplementationMetadata(
    allImplementations: { [key: string]: ImplementationMetadata },
    implementationName: string
  ): ImplementationMetadata {
    const filteredKeys = Object.keys(allImplementations).filter((key) =>
      key.includes(implementationName)
    );
    return allImplementations[filteredKeys[0]];
  }

  // Filter the implementation metadata using the selected implementation name.
  const implementation = getFilteredImplementationMetadata(
    allImplementations,
    implementationName
  );

  return allImplementations ? (
    <ReportComponent implementation={implementation} />
  ) : (
    <LoadingAnimation />
  );
};

const ReportComponent: React.FC<{ implementation: ImplementationMetadata }> = ({
  implementation,
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
                <td>{implementation.name}</td>
              </tr>
              <tr>
                <th>Version:</th>
                <td>{implementation.version}</td>
              </tr>
              <tr>
                <th>Language:</th>
                <td>
                  {mapLanguage(implementation.language)}
                  <span className="text-muted">
                    {implementation.language &&
                      implementation.language_version &&
                      ` (${implementation.language_version || ""})`}
                  </span>
                </td>
              </tr>
              <tr>
                <th>OS:</th>
                <td>
                  {implementation.os || ""}
                  <span className="text-muted">
                    {implementation.os &&
                      implementation.os_version &&
                      ` (${implementation.os_version})`}
                  </span>
                </td>
              </tr>
              <tr>
                <th>Dialects:</th>
                <td>
                  <ul>
                    {implementation.dialects.map(
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
                <td>{implementation.image}</td>
              </tr>
              <tr>
                <th>Homepage:</th>
                {implementation.homepage && (
                  <td>
                    <Link to={implementation.homepage}>
                      {implementation.homepage}
                    </Link>
                  </td>
                )}
              </tr>
              <tr>
                <th>Issues:</th>
                <td>
                  <Link to={implementation.issues}>
                    {implementation.issues}
                  </Link>
                </td>
              </tr>
            </tbody>
          </Table>
        </Card.Body>
      </Card>
      <DialectCompliance implementation={implementation} />
    </Container>
  );
};

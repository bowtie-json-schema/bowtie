import { Card } from "react-bootstrap";
import { useLoaderData, useParams, Link, Navigate } from "react-router-dom";
import { Table, Container } from "react-bootstrap";
import { Implementation } from "../../data/parseReportData";
import LoadingAnimation from "../LoadingAnimation";
import DialectCompliance from "./DialectCompliance";
import { mapLanguage } from "../../data/mapLanguage";
import { versionsBadgeFor } from "../../data/Badge";

export const ImplementationReportView = () => {
  // Fetch all supported implementation's metadata.
  const allImplementations = useLoaderData() as Record<string, Implementation>;

  // Get the selected implementation's name from the URL parameters.
  const { langImplementation } = useParams();
  // FIXME: This magic prefix is duplicated from the backend side,
  //        and probably needs some tweaking for when using a local image.
  const image = langImplementation
    ? `ghcr.io/bowtie-json-schema/${langImplementation}`
    : "";
  const implementation = allImplementations[image];

  // FIXME: Probably redirect to /implementations if/when that's a thing.
  return allImplementations ? (
    implementation ? (
      <ReportComponent implementation={implementation} />
    ) : (
      <Navigate to="/" />
    )
  ) : (
    <LoadingAnimation />
  );
};

const ReportComponent: React.FC<{ implementation: Implementation }> = ({
  implementation,
}) => {
  return (
    <Container className="p-4">
      <Card className="mx-auto mb-3 col-md-9">
        <Card.Header>
          <span className="px-1 text-muted">
            {mapLanguage(implementation.language)}
          </span>

          <span>{implementation.name}</span>
        </Card.Header>

        <Card.Body>
          <Table>
            <tbody>
              <tr>
                <th>Homepage</th>
                <td>
                  <Link to={implementation.homepage}>
                    {implementation.homepage}
                  </Link>
                </td>
              </tr>
              {implementation.documentation && (
                <tr>
                  <th>Documentation</th>
                  <td>
                    <Link to={implementation.documentation}>
                      {implementation.documentation}
                    </Link>
                  </td>
                </tr>
              )}
              <tr>
                <th>Source</th>
                <td>
                  <Link to={implementation.source}>
                    {implementation.source}
                  </Link>
                </td>
              </tr>
              <tr>
                <th>Issues</th>
                <td>
                  <Link to={implementation.issues}>
                    {implementation.issues}
                  </Link>
                </td>
              </tr>
              <tr>
                <th>Version</th>
                <td>{implementation.version}</td>
              </tr>
              <tr>
                <th>Language</th>
                <td>
                  {mapLanguage(implementation.language)}
                  <span className="text-muted">
                    {implementation.language &&
                      implementation.language_version &&
                      ` (${implementation.language_version || ""})`}
                  </span>
                </td>
              </tr>
              {implementation.os && (
                <tr>
                  <th>OS</th>
                  <td>
                    {implementation.os}
                    <span className="text-muted">
                      {implementation.os_version &&
                        ` (${implementation.os_version})`}
                    </span>
                  </td>
                </tr>
              )}
              <tr>
                <th>Supported Dialects</th>
                <td className="col-7">
                  <img
                    alt={implementation.name}
                    className="my-1"
                    src={versionsBadgeFor(implementation).href}
                    style={{ maxWidth: "100%" }}
                  />
                </td>
              </tr>
              {implementation.links && !!implementation.links.length && (
                <tr>
                  <th>Additional Links</th>
                  <td>
                    <ul>
                      {implementation.links.map(
                        ({ description, url }, index: number) => (
                          <li key={index}>
                            <Link to={url ?? ""}>{description}</Link>
                          </li>
                        )
                      )}
                    </ul>
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
      <DialectCompliance implementation={implementation} />
    </Container>
  );
};

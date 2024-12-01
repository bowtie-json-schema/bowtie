import {
  useLoaderData,
  Link,
  Navigate,
  Outlet,
  useNavigate,
} from "react-router";
import Container from "react-bootstrap/Container";
import Card from "react-bootstrap/Card";
import Table from "react-bootstrap/Table";
import Button from "react-bootstrap/Button";

import DialectCompliance from "./DialectCompliance";
import LoadingAnimation from "../LoadingAnimation";
import VersionsTrend from "./VersionsTrend";
import { ImplementationReport } from "../../data/parseReportData";
import { mapLanguage } from "../../data/mapLanguage";
import { EmbedBadgesContextType } from "./EmbedBadges";

interface Props {
  implementationReport: ImplementationReport;
}

export const ImplementationReportView = () => {
  const implementationReport: ImplementationReport | null = useLoaderData();

  return implementationReport === null ? (
    // FIXME: Probably redirect to /implementations if/when that's a thing.
    <Navigate to="/" />
  ) : !implementationReport ? (
    <LoadingAnimation />
  ) : (
    <ReportComponent implementationReport={implementationReport} />
  );
};

const ReportComponent = ({ implementationReport }: Props) => {
  const navigate = useNavigate();
  const { implementation, dialectsCompliance } = implementationReport;

  return (
    <Container className="p-4">
      <Card className="mx-auto mb-3 col-md-9">
        <Card.Header className="d-flex align-items-center justify-content-between">
          <span className="d-flex">
            <span className="pe-2 text-muted">
              {mapLanguage(implementation.language)}
            </span>
            <span>{implementation.name}</span>
          </span>
          <Button
            variant="info"
            size="sm"
            onClick={() => void navigate("badges")}
          >
            Badges
          </Button>
          <Outlet context={implementation satisfies EmbedBadgesContextType} />
        </Card.Header>

        <Card.Body className="overflow-x-auto">
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
                    src={implementation.versionsBadge().href()}
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
                        ({ description, url }, index) => (
                          <li key={index}>
                            <Link to={url ?? ""}>{description}</Link>
                          </li>
                        ),
                      )}
                    </ul>
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
      <DialectCompliance
        implementation={implementation}
        dialectsCompliance={dialectsCompliance}
      />
      {implementation.versions && (
        <VersionsTrend implementation={implementation} />
      )}
    </Container>
  );
};

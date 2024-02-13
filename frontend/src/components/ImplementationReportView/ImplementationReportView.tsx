import { Card, Table, Container } from "react-bootstrap";
import { useLoaderData, useParams, Link, Navigate } from "react-router-dom";
import {
  Eye,
  StarFill,
  BoxFill,
  ArrowCounterclockwise,
  RecordCircle,
  Tools,
} from "react-bootstrap-icons";
import { Implementation } from "../../data/parseReportData";
import LoadingAnimation from "../LoadingAnimation";
import DialectCompliance from "./DialectCompliance";
import { mapLanguage } from "../../data/mapLanguage";
import { formatDate } from "../../utils/formatDate";

interface LoaderData {
  allReportsData: Record<string, Implementation>;
  implementationStatsData: Implementation[];
}

export const ImplementationReportView = () => {
  // Fetch all supported implementation's metadata.
  const { allReportsData, implementationStatsData } =
    useLoaderData() as LoaderData;

  // Get the selected implementation's name from the URL parameters.
  const { langImplementation } = useParams();
  // FIXME: This magic prefix is duplicated from the backend side,
  //        and probably needs some tweaking for when using a local image.
  const image = langImplementation
    ? `ghcr.io/bowtie-json-schema/${langImplementation}`
    : "";

  const implementationStats: Implementation = implementationStatsData.find(
    (impl: Implementation) => impl.source === allReportsData[image].source,
  )!;

  const implementation = {
    ...allReportsData[image],
    ...implementationStats,
  };

  // FIXME: Probably redirect to /implementations if/when that's a thing.
  return allReportsData ? (
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
      <Card className="mx-auto mb-3 w-75">
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
                <th>Homepage:</th>
                <td>
                  <Link to={implementation.homepage}>
                    {implementation.homepage}
                  </Link>
                </td>
              </tr>
              {implementation.documentation && (
                <tr>
                  <th>Documentation:</th>
                  <td>
                    <Link to={implementation.documentation}>
                      {implementation.documentation}
                    </Link>
                  </td>
                </tr>
              )}
              <tr>
                <th>Source:</th>
                <td>
                  <Link to={implementation.source}>
                    {implementation.source}
                  </Link>
                </td>
              </tr>
              {implementation.last_release_date && (
                <tr>
                  <th>
                    <div className="d-flex align-items-center">
                      <BoxFill size={17} style={{ marginRight: "5px" }} />
                      Last Release Date:
                    </div>
                  </th>
                  <td>{formatDate(implementation.last_release_date)}</td>
                </tr>
              )}
              {implementation.last_commit_date && (
                <tr>
                  <th>
                    <div className="d-flex align-items-center">
                      <ArrowCounterclockwise
                        size={20}
                        style={{ marginRight: "5px" }}
                      />
                      Last Commit Date:
                    </div>
                  </th>
                  <td>{formatDate(implementation.last_commit_date)}</td>
                </tr>
              )}
              {implementation.stars_count !== undefined &&
                implementation.stars_count >= 0 && (
                  <tr>
                    <th>
                      <div className="d-flex align-items-center">
                        <StarFill
                          color="yellow"
                          size={20}
                          style={{ marginRight: "5px" }}
                        />
                        Stars:
                      </div>
                    </th>
                    <td>{implementation.stars_count}</td>
                  </tr>
                )}
              {implementation.watchers_count !== undefined &&
                implementation.watchers_count >= 0 && (
                  <tr>
                    <th>
                      <div className="d-flex align-items-center">
                        <Eye size={20} style={{ marginRight: "5px" }} />
                        Watchers:
                      </div>
                    </th>
                    <td>{implementation.watchers_count}</td>
                  </tr>
                )}
              {implementation.open_issues_count !== undefined &&
                implementation.open_issues_count >= 0 && (
                  <tr>
                    <th>
                      <div className="d-flex align-items-center">
                        <RecordCircle
                          size={20}
                          style={{ marginRight: "5px" }}
                        />
                        Open Issues:
                      </div>
                    </th>
                    <td>{implementation.open_issues_count}</td>
                  </tr>
                )}
              {implementation.open_prs_count !== undefined &&
                implementation.open_prs_count >= 0 && (
                  <tr>
                    <th>
                      <div className="d-flex align-items-center">
                        <Tools size={17} style={{ marginRight: "5px" }} />
                        Open Pull Requests:
                      </div>
                    </th>
                    <td>{implementation.open_prs_count}</td>
                  </tr>
                )}
              <tr>
                <th>Issues:</th>
                <td>
                  <Link to={implementation.issues}>
                    {implementation.issues}
                  </Link>
                </td>
              </tr>
              {implementation.version && (
                <tr>
                  <th>Version:</th>
                  <td>{implementation.version}</td>
                </tr>
              )}
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
              {implementation.os && (
                <tr>
                  <th>OS:</th>
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
                <th>Supported Dialects:</th>
                <td>
                  <ul>
                    {implementation.dialects.map(
                      (dialect: string, index: number) => (
                        <li key={index}>{dialect}</li>
                      ),
                    )}
                  </ul>
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

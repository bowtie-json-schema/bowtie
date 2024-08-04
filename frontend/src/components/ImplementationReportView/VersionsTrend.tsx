import React, { useEffect, useState } from "react";
import Card from "react-bootstrap/Card";
import Dropdown from "react-bootstrap/Dropdown";
import {
  CartesianGrid,
  LineChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Line,
  TooltipProps,
  Label,
} from "recharts";
import {
  NameType,
  ValueType,
} from "recharts/types/component/DefaultTooltipContent";
import { Payload } from "recharts/types/component/DefaultLegendContent";
import semverCompare from "semver/functions/compare";

import LoadingAnimation from "../LoadingAnimation";
import Dialect from "../../data/Dialect";
import Implementation from "../../data/Implementation";
import {
  ImplementationReport,
  prepareVersionsComplianceReport,
  Totals,
} from "../../data/parseReportData";

interface Props {
  implementation: Implementation;
  versionsCompliance: NonNullable<ImplementationReport["versionsCompliance"]>;
}

interface TrendData extends Partial<Totals> {
  version: string;
  unsuccessfulTests: number;
}

const VersionsTrend: React.FC<Props> = ({
  implementation,
  versionsCompliance: initialVersionsCompliance,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDialect, setSelectedDialect] = useState(
    initialVersionsCompliance.keys().next().value as Dialect
  );
  const [versionsCompliance, setVersionsCompliance] = useState(
    initialVersionsCompliance
  );
  const [trendData, setTrendData] = useState<TrendData[]>([]);

  useEffect(() => {
    void (async () => {
      setIsLoading(true);

      try {
        if (!versionsCompliance.has(selectedDialect)) {
          const selectedDialectData =
            await implementation.fetchVersionedReportsFor(
              selectedDialect,
              implementation.versions!
            );

          setVersionsCompliance((prev) =>
            new Map(prev).set(
              selectedDialect,
              prepareVersionsComplianceReport(selectedDialectData).get(
                selectedDialect
              )!
            )
          );
        }

        setTrendData(
          Array.from(versionsCompliance.get(selectedDialect)!)
            .sort(([versionA], [versionB]) => semverCompare(versionA, versionB))
            .map(([version, data]) => ({
              version: `v${version}`,
              unsuccessfulTests:
                data.erroredTests! + data.failedTests! + data.skippedTests!,
              ...data,
            }))
        );
      } catch (error) {
        setTrendData([]);
      } finally {
        setIsLoading(false);
      }
    })();
  }, [selectedDialect, implementation, versionsCompliance]);

  return (
    <Card className="mx-auto mb-3 col-md-9">
      <Card.Header>Versions Trend</Card.Header>
      <Card.Body className="p-3" style={{ height: "35rem" }}>
        <Card className="p-3 h-100">
          <div className="mb-4 d-flex justify-content-end">
            <Dropdown
              onSelect={(dialectShortName) =>
                setSelectedDialect(Dialect.withName(dialectShortName!))
              }
            >
              <Dropdown.Toggle variant="outline-dark">
                {selectedDialect.prettyName}
              </Dropdown.Toggle>
              <Dropdown.Menu>
                {Dialect.newest_to_oldest()
                  .filter((dialect) => dialect != selectedDialect)
                  .map((dialect) => (
                    <Dropdown.Item
                      key={dialect.shortName}
                      eventKey={dialect.shortName}
                    >
                      {dialect.prettyName}
                    </Dropdown.Item>
                  ))}
              </Dropdown.Menu>
            </Dropdown>
          </div>
          {isLoading ? (
            <LoadingAnimation />
          ) : trendData.length === 0 ? (
            <div className="d-flex justify-content-center align-items-center h-100">
              {`None of the versions of ${implementation.id} support ${selectedDialect.prettyName}.`}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={trendData}
                margin={{
                  top: 10,
                  right: 40,
                  left: 10,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="version" />
                <YAxis>
                  <Label
                    angle={-90}
                    position="insideLeft"
                    style={{
                      textAnchor: "middle",
                      fill: "#212529",
                    }}
                    offset={9}
                  >
                    Total Unsuccessful Tests
                  </Label>
                </YAxis>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  payload={
                    [
                      { value: `${implementation.id} versions`, type: "line" },
                    ] satisfies Payload[]
                  }
                />
                <Line
                  type="linear"
                  dataKey="unsuccessfulTests"
                  stroke="#f05f80"
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Card>
      </Card.Body>
    </Card>
  );
};

const CustomTooltip = ({
  active,
  payload,
  label,
}: TooltipProps<ValueType, NameType>) => {
  if (active && payload?.length) {
    return (
      <div className="border border-secondary rounded p-3 bg-white">
        <span className="fw-bold mb-1">{label}</span>
        <span className="d-block mb-1">
          erroredTests:{" "}
          <span className="fw-semibold">
            {(payload[0].payload as TrendData).erroredTests}
          </span>
        </span>
        <span className="d-block mb-1">
          failedTests:{" "}
          <span className="fw-semibold">
            {(payload[0].payload as TrendData).failedTests}
          </span>
        </span>
        <span className="d-block mb-1">
          skippedTests:{" "}
          <span className="fw-semibold">
            {(payload[0].payload as TrendData).skippedTests}
          </span>
        </span>
      </div>
    );
  }

  return null;
};

export default VersionsTrend;

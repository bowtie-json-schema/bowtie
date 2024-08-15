import { FC, useContext, useEffect, useState } from "react";
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

import LoadingAnimation from "../LoadingAnimation";
import Dialect from "../../data/Dialect";
import Implementation from "../../data/Implementation";
import sortVersions from "../../data/sortVersions";
import {
  ImplementationReport,
  prepareVersionsComplianceReport,
  Totals,
} from "../../data/parseReportData";
import { ThemeContext } from "../../context/ThemeContext";

interface Props {
  implementation: Implementation;
}

interface TrendData extends Partial<Totals> {
  version: string;
  unsuccessfulTests: number;
}

const VersionsTrend: FC<Props> = ({ implementation }) => {
  const { isDarkMode } = useContext(ThemeContext);

  const [isLoading, setIsLoading] = useState(false);
  const [selectedDialect, setSelectedDialect] = useState<Dialect>();
  const [versionsCompliance, setVersionsCompliance] = useState<
    NonNullable<ImplementationReport["versionsCompliance"]>
  >(new Map());
  const [trendData, setTrendData] = useState<TrendData[]>([]);

  const onDialectSelected = (dialectShortName: string | null) => {
    void (async () => {
      setIsLoading(true);
      const dialect = Dialect.withName(dialectShortName!);
      setSelectedDialect(dialect);
      try {
        if (!versionsCompliance.has(dialect)) {
          const dialectData = await implementation.fetchVersionedReportsFor(
            dialect,
            implementation.versions!,
          );
          setVersionsCompliance((prev) =>
            new Map(prev).set(
              dialect,
              prepareVersionsComplianceReport(dialectData).get(dialect)!,
            ),
          );
        }
      } catch (error) {
        setTrendData([]);
      } finally {
        setIsLoading(false);
      }
    })();
  };

  useEffect(() => {
    if (selectedDialect && versionsCompliance.has(selectedDialect)) {
      setTrendData(
        Array.from(versionsCompliance.get(selectedDialect)!)
          .sort(([versionA], [versionB]) => sortVersions(versionA, versionB))
          .map(([version, data]) => ({
            version: `v${version}`,
            unsuccessfulTests:
              data.erroredTests! + data.failedTests! + data.skippedTests!,
            ...data,
          })),
      );
    }
  }, [selectedDialect, versionsCompliance]);

  return (
    <Card className="mx-auto mb-3 col-md-9">
      <Card.Header>Versions Trend</Card.Header>
      <Card.Body className="p-3" style={{ height: "35rem" }}>
        <Card className="p-3 h-100">
          <div className="mb-4 d-flex justify-content-end">
            <Dropdown onSelect={onDialectSelected}>
              <Dropdown.Toggle
                variant={isDarkMode ? "outline-light" : "outline-dark"}
              >
                {selectedDialect ? selectedDialect.prettyName : "Dialects"}
              </Dropdown.Toggle>
              <Dropdown.Menu>
                {Dialect.newest_to_oldest()
                  .filter(
                    (dialect) =>
                      !selectedDialect || dialect !== selectedDialect,
                  )
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
          {!selectedDialect ? (
            <div className="d-flex justify-content-center align-items-center h-100">
              {`Select a dialect from the dropdown to see the versions trend data
              of ${implementation.id} on it's test suite.`}
            </div>
          ) : isLoading ? (
            <LoadingAnimation />
          ) : !trendData.length ? (
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
                <CartesianGrid
                  stroke={isDarkMode ? "#666" : "#ccc"}
                  strokeDasharray="3 3"
                />
                <XAxis
                  stroke={isDarkMode ? "#ddd" : "#000"}
                  dataKey="version"
                />
                <YAxis stroke={isDarkMode ? "#ddd" : "#000"}>
                  <Label
                    angle={-90}
                    position="insideLeft"
                    style={{
                      textAnchor: "middle",
                      fill: isDarkMode ? "#ddd" : "#000",
                    }}
                    offset={9}
                  >
                    Total Unsuccessful Tests
                  </Label>
                </YAxis>
                <Tooltip content={<CustomTooltip isDarkMode={isDarkMode!} />} />
                <Legend
                  payload={
                    [
                      {
                        value: `${implementation.id} versions`,
                        type: "line",
                        color: isDarkMode ? "#fff" : "#000",
                      },
                    ] satisfies Payload[]
                  }
                />
                <Line
                  type="linear"
                  dataKey="unsuccessfulTests"
                  stroke={isDarkMode ? "#ff007f" : "#f05f80"}
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
  isDarkMode,
}: TooltipProps<ValueType, NameType> & { isDarkMode: boolean }) => {
  if (active && payload?.length) {
    return (
      <div
        className={`border border-secondary rounded p-3 ${
          isDarkMode ? "bg-dark border-light" : "bg-white border-secondary"
        }`}
      >
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

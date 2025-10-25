import { useCallback, useContext, useEffect, useMemo, useState } from "react";
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
  Label,
} from "recharts";


import LoadingAnimation from "../LoadingAnimation";
import Dialect from "../../data/Dialect";
import Implementation from "../../data/Implementation";
import sortVersions from "../../data/sortVersions";
import { Totals } from "../../data/parseReportData";
import { ThemeContext } from "../../context/ThemeContext";

interface Props {
  implementation: Implementation;
}

interface TrendData extends Partial<Totals> {
  version: string;
  totalUnsuccessfulTests: number;
}

const VersionsTrend = ({ implementation }: Props) => {
  const { isDarkMode } = useContext(ThemeContext);

  const [isLoading, setIsLoading] = useState(false);
  const [selectedDialect, setSelectedDialect] = useState(Dialect.latest());
  const [dialectsTrendData, setDialectsTrendData] = useState<
    Map<Dialect, TrendData[]>
  >(new Map());

  const fetchDialectTrendData = useCallback(async () => {
    setIsLoading(true);
    try {
      const versionedReports =
        await implementation.fetchVersionedReportsFor(selectedDialect);

      setDialectsTrendData((prev) =>
        new Map(prev).set(
          selectedDialect,
          Array.from(versionedReports)
            .sort(([versionA], [versionB]) => sortVersions(versionA, versionB))
            .map(([version, data]) => {
              const { failedTests, erroredTests, skippedTests } =
                data.implementationsResults.values().next().value!.totals;

              return {
                version: `v${version}`,
                failedTests,
                erroredTests,
                skippedTests,
                totalUnsuccessfulTests:
                  failedTests! + erroredTests! + skippedTests!,
              };
            }),
        ),
      );
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      setDialectsTrendData((prev) => new Map(prev).set(selectedDialect, []));
    } finally {
      setIsLoading(false);
    }
  }, [selectedDialect, implementation]);

  const shouldFetchDialectTrendData = useMemo(
    () => !dialectsTrendData.has(selectedDialect),
    [selectedDialect, dialectsTrendData],
  );

  useEffect(() => {
    if (shouldFetchDialectTrendData) {
      void fetchDialectTrendData();
    }
  }, [shouldFetchDialectTrendData, fetchDialectTrendData]);

  const filteredDialects = useMemo(
    () =>
      Dialect.newestToOldest().filter((dialect) => dialect != selectedDialect),
    [selectedDialect],
  );

  const handleDialectSelect = useCallback(
    (shortName: string | null) =>
      setSelectedDialect(Dialect.withName(shortName!)),
    [],
  );



  return (
    <Card className="mx-auto mb-3 col-md-9">
      <Card.Header>Versions Trend</Card.Header>
      <Card.Body className="p-3" style={{ height: "35rem" }}>
        <Card className="p-3 h-100">
          <div className="mb-4 d-flex justify-content-end">
            <Dropdown onSelect={handleDialectSelect}>
              <Dropdown.Toggle
                variant={isDarkMode ? "outline-light" : "outline-dark"}
              >
                {selectedDialect.prettyName}
              </Dropdown.Toggle>
              <Dropdown.Menu>
                {filteredDialects.map((dialect) => (
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
          {isLoading || !dialectsTrendData.has(selectedDialect) ? (
            <LoadingAnimation />
          ) : !dialectsTrendData.get(selectedDialect)!.length ? (
            <div className="d-flex justify-content-center align-items-center h-100">
              {`None of the versions of ${implementation.id} support ${selectedDialect.prettyName}.`}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={dialectsTrendData.get(selectedDialect)}
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
                <Legend />
                <Line
                  name={`${implementation.id} versions`}
                  type="linear"
                  dataKey="totalUnsuccessfulTests"
                  stroke="#ff007f"
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

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string | number;
  isDarkMode: boolean;
}

interface TooltipPayload {
  payload: TrendData;
}

const CustomTooltip = (props: CustomTooltipProps) => {
  const { active, payload, label, isDarkMode } = props;
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
            {payload[0].payload.erroredTests}
          </span>
        </span>
        <span className="d-block mb-1">
          failedTests:{" "}
          <span className="fw-semibold">
            {payload[0].payload.failedTests}
          </span>
        </span>
        <span className="d-block mb-1">
          skippedTests:{" "}
          <span className="fw-semibold">
            {payload[0].payload.skippedTests}
          </span>
        </span>
      </div>
    );
  }

  return null;
};

export default VersionsTrend;

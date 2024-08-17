import {
  BenchmarkReportData,
  BenchmarkGroupResult,
} from "../../data/parseBenchmarkData";
import ListGroup from "react-bootstrap/ListGroup";
import BenchmarkTypeResultSection from "./BenchmarkTypeResultSection";
import Card from "react-bootstrap/Card";

const BenchmarkResultsSection = ({
  benchmarkReportData,
}: {
  benchmarkReportData: BenchmarkReportData;
}) => {
  const benchmarkResults = benchmarkReportData.results;
  const resultsByBenchmarkType = benchmarkResults.reduce(
    (acc, item) => {
      if (!acc[item.benchmarkType]) {
        acc[item.benchmarkType] = [];
      }
      acc[item.benchmarkType].push(item);
      return acc;
    },
    {} as Record<string, BenchmarkGroupResult[]>,
  );

  return (
    <Card className="mx-auto mb-3">
      <Card.Header>Benchmark Results</Card.Header>
      <ListGroup as="ol">
        {Object.entries(resultsByBenchmarkType).map(
          ([benchmarkType, benchmarkResults]) => (
            <BenchmarkTypeResultSection
              key={benchmarkType}
              benchmarkType={benchmarkType}
              benchmarkResults={benchmarkResults}
            />
          ),
        )}
      </ListGroup>
    </Card>
  );
};

export default BenchmarkResultsSection;

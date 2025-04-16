import Card from "react-bootstrap/Card";
import {
  BenchmarkGroupResult,
  geometricMean as gMean,
} from "../../data/parseBenchmarkData";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Rectangle,
  ResponsiveContainer,
} from "recharts";
import { useContext, useMemo } from "react";
import { ThemeContext } from "../../context/ThemeContext";
import { mean, min, max } from "mathjs";

const BenchmarkSummarySection = ({
  benchmarkResults,
}: {
  benchmarkResults: BenchmarkGroupResult[];
}) => {
  const { isDarkMode } = useContext(ThemeContext);
  const textColor = isDarkMode ? "white" : "black";

  const benchmarkRankings = useMemo(() => {
    const resultsForImplementation: Record<string, number[][]> = {};

    benchmarkResults.map((benchmarkGroupResult) => {
      benchmarkGroupResult.benchmarkResults.map((benchmarkResult) => {
        benchmarkResult.testResults.map((testResult) => {
          testResult.implementationResults.map((implementationResult) => {
            if (!implementationResult.errored) {
              if (
                !resultsForImplementation[implementationResult.implementationId]
              ) {
                resultsForImplementation[
                  implementationResult.implementationId
                ] = [implementationResult.values];
              } else {
                resultsForImplementation[
                  implementationResult.implementationId
                ].push(implementationResult.values);
              }
            }
          });
        });
      });
    });

    const meanForImplementation: Record<string, number> = {};

    Object.entries(resultsForImplementation).map(
      ([implementationId, implementationResults]) => {
        const means: number[] = implementationResults.map(
          (implementationResult) => {
            return mean(implementationResult);
          },
        );
        const geometricMean = gMean(means);
        meanForImplementation[implementationId] = geometricMean;
      },
    );

    let chartData: Record<string, string>[] = Object.entries(
      meanForImplementation,
    ).map(([implementationId, geometricMean]) => {
      return {
        implementation_name: implementationId,
        mean_time: Number(geometricMean).toFixed(4),
      };
    });

    chartData = chartData.sort((a, b) =>
      a.implementation_name.localeCompare(b.implementation_name),
    );

    return chartData;
  }, [benchmarkResults]);

  return (
    <Card className="mx-auto mb-3 d-none d-sm-block">
      <Card.Header>Benchmark Summary</Card.Header>
      <ResponsiveContainer
        width="100%"
        // Either height or width something needs to be specified for recharts
        height={min(max(150, benchmarkRankings.length * 45), 750)}
      >
        <BarChart
          data={benchmarkRankings}
          layout="vertical"
          className="p-3 text-primary"
          margin={{ bottom: 35 }}
        >
          <XAxis
            label={{
              value: "Average time taken in seconds (shorter is better)",
              position: "bottom",
              offset: 10,
            }}
            type="number"
            tick={{ fill: textColor }}
          />
          <YAxis
            label={
              // Handling case when the label won't fit because of too few rows
              benchmarkRankings.length > 5
                ? {
                    value: "Implementation Name",
                    angle: -90,
                    position: "insideLeft",
                  }
                : {}
            }
            width={310}
            dataKey="implementation_name"
            type="category"
            tick={{ fill: textColor }}
          />

          <Tooltip />
          <Bar
            dataKey="mean_time"
            fill="#0d6efd"
            activeBar={<Rectangle fill="#212529" />}
          />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default BenchmarkSummarySection;

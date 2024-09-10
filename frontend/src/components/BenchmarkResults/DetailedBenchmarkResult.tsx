import { useMemo } from "react";

import {
  BenchmarkGroupResult,
  TestResult,
} from "../../data/parseBenchmarkData";
import Card from "react-bootstrap/Card";
import TestResultTable from "./TestResultTable";
import Accordion from "react-bootstrap/Accordion";

const DetailedBenchmarkResult = ({
  benchmarkGroupResult,
}: {
  benchmarkGroupResult: BenchmarkGroupResult;
}) => {
  const nonCommonBenchmarkResult = benchmarkGroupResult.benchmarkResults.at(-1);

  const commonTestResults: TestResult[] = useMemo(() => {
    let commonTests = new Set(
      benchmarkGroupResult.benchmarkResults[0].testResults.map(
        (test) => test.description,
      ),
    );

    benchmarkGroupResult.benchmarkResults
      .slice(1)
      .forEach((benchmarkResult) => {
        const currentDescriptions = new Set(
          benchmarkResult.testResults.map((test) => test.description),
        );
        commonTests = new Set(
          [...commonTests].filter((test) => currentDescriptions.has(test)),
        );
      });

    const commonTest = [...commonTests][0];

    const commonTestResults = benchmarkGroupResult.benchmarkResults.reduce<
      TestResult[]
    >((acc, benchmarkResult) => {
      const testResult = benchmarkResult.testResults.find(
        (test: TestResult) => test.description === commonTest,
      );
      if (testResult) {
        acc.push({
          description: benchmarkResult.name,
          implementationResults: testResult.implementationResults,
        });
      }
      return acc;
    }, []);
    return commonTestResults;
  }, [benchmarkGroupResult.benchmarkResults]);

  return (
    <>
      {benchmarkGroupResult.benchmarkResults.length > 0 && (
        <Card className="mx-auto mb-3">
          <Card.Header>Detailed Results</Card.Header>
          <Accordion className="p-3">
            {benchmarkGroupResult.varyingParameter && (
              <TestResultTable
                testResults={commonTestResults}
                heading={`Tests with varying ${benchmarkGroupResult.varyingParameter}`}
              />
            )}
            {nonCommonBenchmarkResult && (
              <TestResultTable
                testResults={nonCommonBenchmarkResult.testResults}
                heading={`Tests with ${nonCommonBenchmarkResult.name}`}
              />
            )}
          </Accordion>
        </Card>
      )}
    </>
  );
};

export default DetailedBenchmarkResult;

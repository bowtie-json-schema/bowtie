import { useMemo } from "react";

import { useSearchParams } from "./hooks/useSearchParams.ts";
import { BenchmarkReportData } from "./data/parseBenchmarkData.ts";
import BenchmarkRunInfoSection from "./components/RunInfo/BenchmarkRunInfoSection.tsx";
import BenchmarkResultsSection from "./components/BenchmarkResults/BenchmarkResultsSection.tsx";
import BenchmarkSummarySection from "./components/BenchmarkResults/BenchmarkSummarySection.tsx";
import { BenchmarkFilterSection } from "./components/Filter/BenchmarkFilterSection.tsx";

export const BenchmarkReportView = ({
  benchmarkReportData,
  topPageInfoSection,
}: {
  benchmarkReportData: BenchmarkReportData;
  topPageInfoSection?: React.ReactElement;
}) => {
  const params = useSearchParams();

  const languages = useMemo(() => {
    const langs = new Set<string>();
    for (const each of benchmarkReportData.metadata.implementations.values()) {
      langs.add(each.language);
    }
    return Array.from(langs);
  }, [benchmarkReportData]);

  const benchmarkTypes = useMemo(() => {
    const types = new Set<string>();
    for (const each of benchmarkReportData.results) {
      types.add(each.benchmarkType);
    }
    return Array.from(types);
  }, [benchmarkReportData]);

  const filteredBenchmarkReportData = useMemo(() => {
    const filteredData = { ...benchmarkReportData };
    const selectedLanguages = params.getAll("language");
    const selectedTypes = params.getAll("benchmark_type");
    const implementationNames = Array.from(
      benchmarkReportData.metadata.implementations,
    )
      .filter(([, implementationData]) =>
        selectedLanguages.includes(implementationData.language),
      )
      .map(([implementationId]) => implementationId);

    filteredData.results = benchmarkReportData.results
      .map((group) => ({
        ...group,
        benchmarkResults: group.benchmarkResults
          .map((benchmark) => ({
            ...benchmark,
            testResults: benchmark.testResults
              .map((test) => ({
                ...test,
                implementationResults: test.implementationResults.filter(
                  (result) =>
                    implementationNames.includes(result.implementationId) ||
                    implementationNames.length == 0,
                ),
              }))
              .filter((test) => test.implementationResults.length > 0),
          }))
          .filter((benchmark) => benchmark.testResults.length > 0),
      }))
      .filter(
        (group) =>
          group.benchmarkResults.length > 0 &&
          (selectedTypes.length == 0 ||
            selectedTypes.includes(group.benchmarkType)),
      );
    return filteredData;
  }, [benchmarkReportData, params]);

  return (
    <main className="container-lg">
      <div className="col col-lg-8 mx-auto">
        {topPageInfoSection}
        <BenchmarkRunInfoSection
          benchmarkRunMetadata={filteredBenchmarkReportData.metadata}
        />
        <BenchmarkFilterSection
          languages={languages}
          benchmarkTypes={benchmarkTypes}
        />
        <BenchmarkSummarySection
          benchmarkResults={filteredBenchmarkReportData.results}
        />
        <BenchmarkResultsSection
          benchmarkReportData={filteredBenchmarkReportData}
        />
      </div>
    </main>
  );
};

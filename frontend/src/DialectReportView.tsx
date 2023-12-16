// @ts-ignore
import CasesSection from "./components/Cases/CasesSection";
// @ts-ignore
import RunInfoSection from "./components/RunInfo/RunInfoSection";
// @ts-ignore
import SummarySection from "./components/Summary/SummarySection";
import { useMemo } from "react";
import { ReportData, Case } from "./data/parseReportData.ts";
import { FilterSection } from "./components/FilterSection.tsx";
import { useSearchParams } from "./hooks/useSearchParams.ts";

export const DialectReportView = ({
  reportData,
}: {
  reportData: ReportData;
}) => {
  const params = useSearchParams();

  const languages = useMemo(() => {
    const langs = Array.from(reportData.implementations.values()).map(
      (impl) => impl.metadata.language,
    );
    return Array.from(new Set(langs).values());
  }, [reportData]);

  const Cases: Map<number, Case> = reportData.cases;
  const vocabularies: string[] = useMemo(() => {
    const vocabSet: Set<string> = new Set();

    Array.from(Cases.values())
      .filter((value) => !!value.registry)
      .forEach((value) => {
        const registry = value.registry!;
        Object.keys(registry).forEach((url) => {
          const vocabObject = (registry[url] as any).$vocabulary;
          if (vocabObject) {
            Object.keys(vocabObject).forEach((key) => {
              const segments = key.split("/");
              vocabSet.add(segments[segments.length - 1]);
            });
          }
        });
      });

    return Array.from(vocabSet);
  }, [reportData]);

  // console.log(vocabularies);
  const filteredData = useMemo(() => {
    let filteredData = reportData;
    if (params.getAll("language").length) {
      const filteredArray = Array.from(
        reportData.implementations.entries(),
      ).filter(([, data]) =>
        params.getAll("language").includes(data.metadata.language),
      );
      filteredData = { ...reportData, implementations: new Map(filteredArray) };
    }
    return filteredData;
  }, [reportData, params]);

  return (
    <div>
      <div className="container p-4">
        <RunInfoSection runInfo={filteredData.runInfo} />
        <FilterSection languages={languages} vocabularies={vocabularies} />
        <SummarySection reportData={filteredData} />
        <CasesSection reportData={filteredData} />
      </div>
    </div>
  );
};

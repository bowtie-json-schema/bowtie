import CasesSection from "./components/Cases/CasesSection";
import BowtieInfoSection from "./components/BowtieInfo/BowtieInfoSection";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import { useMemo } from "react";
import { Implementation, ReportData } from "./data/parseReportData.ts";
import { FilterSection } from "./components/FilterSection.tsx";
import { useSearchParams } from "./hooks/useSearchParams.ts";

export const DialectReportView = ({
  reportData,
  prevImplementations,
}: {
  reportData: ReportData;
  prevImplementations?: Record<string, Implementation> | null;
}) => {
  const params = useSearchParams();

  const languages = useMemo(() => {
    const langs = Array.from(reportData.implementations.values()).map(
      (impl) => impl.metadata.language,
    );
    return Array.from(new Set(langs).values());
  }, [reportData]);

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
        <BowtieInfoSection />
        <RunInfoSection runInfo={filteredData.runInfo} />
        <FilterSection languages={languages} />
        <SummarySection reportData={filteredData} prevImplementations={prevImplementations}/>
        <CasesSection reportData={filteredData} />
      </div>
    </div>
  );
};

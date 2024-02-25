import CasesSection from "./components/Cases/CasesSection";
import BowtieInfoSection from "./components/BowtieInfo/BowtieInfoSection";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import { useMemo } from "react";
import { ReportData } from "./data/parseReportData.ts";
import { FilterSection } from "./components/FilterSection.tsx";
import { useSearchParams } from "./hooks/useSearchParams.ts";

export const DialectReportView = ({
  reportData,
}: {
  reportData: ReportData;
}) => {
  const params = useSearchParams();
  
  function showAboutBowtie() {
    const initialUrl = `${window.location.protocol}//${window.location.host}${window.location.pathname}`;
    const currentUrl = window.location.href;
    const validUrls = [
      `${initialUrl}#/#cases`,
      `${initialUrl}#/#summary`,
      `${initialUrl}#/#run-info`,
      `${initialUrl}#/`,
    ];
  
    return validUrls.includes(currentUrl);
  }

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
    <main className="container-lg">
      <div className="col col-lg-8 mx-auto">
        {showAboutBowtie() && <BowtieInfoSection />}
        <RunInfoSection runInfo={filteredData.runInfo} />
        <FilterSection languages={languages} />
        <SummarySection reportData={filteredData} />
        <CasesSection reportData={filteredData} />
      </div>
    </main>
  );
};

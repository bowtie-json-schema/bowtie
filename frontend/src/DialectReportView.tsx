import CasesSection from "./components/Cases/CasesSection";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import { useMemo } from "react";
import {
  Implementation,
  ImplementationData,
  ReportData,
} from "./data/parseReportData.ts";
import { FilterSection } from "./components/FilterSection.tsx";
import { useSearchParams } from "./hooks/useSearchParams.ts";

export const DialectReportView = ({
  reportData,
  topPageInfoSection,
  allImplementationsData,
}: {
  reportData: ReportData;
  topPageInfoSection?: React.ReactElement;
  allImplementationsData: Record<string, Implementation>;
}) => {
  const params = useSearchParams();
  const languages = useMemo(() => {
    const langs = Array.from(reportData.implementations.values()).map(
      (impl) => impl.metadata.language
    );
    return Array.from(new Set(langs).values());
  }, [reportData]);

  const filteredReportData = useMemo(() => {
    const filteredData = { ...reportData };
    const selectedLanguages = params.getAll("language");

    if (selectedLanguages.length > 0) {
      const filteredReportArray = Array.from(
        reportData.implementations.entries()
      ).filter(([, data]) =>
        selectedLanguages.includes(data.metadata.language)
      );
      filteredData.implementations = new Map(filteredReportArray);
    }

    return filteredData;
  }, [reportData, params]);

  const filteredOtherImplementationsData = useMemo(() => {
    const selectedLanguages = params.getAll("language");
    const availableLanguages =
      selectedLanguages.length > 0 ? selectedLanguages : languages;

    return filterOtherImplementations(
      allImplementationsData,
      availableLanguages,
      filteredReportData.implementations
    );
  }, [
    params,
    allImplementationsData,
    languages,
    filteredReportData.implementations,
  ]);

  return (
    <main className="container-lg">
        {topPageInfoSection}
        <RunInfoSection runInfo={filteredReportData.runInfo} />
        <FilterSection languages={languages} />
        <SummarySection
          reportData={filteredReportData}
          otherImplementationsData={filteredOtherImplementationsData}
        />
        <CasesSection reportData={filteredReportData} />
    </main>
  );
};

const filterOtherImplementations = (
  allImplementationsData: Record<string, Implementation>,
  langs: string[],
  filteredReportImplementationsMap: Map<string, ImplementationData>
): Record<string, Implementation> => {
  const filteredOtherImplementationsArray = Object.entries(
    allImplementationsData
  )
    .filter(([, impl]) => langs.includes(impl.language))
    .filter(([key]) => !filteredReportImplementationsMap.has(key));
  return Object.fromEntries(filteredOtherImplementationsArray);
};
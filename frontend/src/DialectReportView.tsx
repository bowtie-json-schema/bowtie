import CasesSection from "./components/Cases/CasesSection";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import { useMemo } from "react";
import {
  Implementation,
  ImplementationResults,
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
    const langs = new Set<string>();
    for (const each of reportData.runMetadata.implementations.values()) {
      langs.add(each.language);
    }
    return Array.from(langs);
  }, [reportData]);

  const filteredReportData = useMemo(() => {
    const filteredData = { ...reportData };
    const selectedLanguages = params.getAll("language");

    if (selectedLanguages.length > 0) {
      const filteredReportArray = Array.from(
        reportData.implementationsResults.entries()
      ).filter(([id]) =>
        selectedLanguages.includes(
          reportData.runMetadata.implementations.get(id)!.language
        )
      );
      filteredData.implementationsResults = new Map(filteredReportArray);
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
      filteredReportData.implementationsResults
    );
  }, [
    params,
    allImplementationsData,
    languages,
    filteredReportData.implementationsResults,
  ]);

  return (
    <main className="container-lg">
      <div className="col col-lg-8 mx-auto">
        {topPageInfoSection}
        <RunInfoSection runMetadata={filteredReportData.runMetadata} />
        <FilterSection languages={languages} />
        <SummarySection
          reportData={filteredReportData}
          otherImplementationsData={filteredOtherImplementationsData}
        />
        <CasesSection reportData={filteredReportData} />
      </div>
    </main>
  );
};

const filterOtherImplementations = (
  allImplementationsData: Record<string, Implementation>,
  langs: string[],
  filteredReportImplementationsMap: Map<string, ImplementationResults>
): Record<string, Implementation> => {
  const filteredOtherImplementationsArray = Object.entries(
    allImplementationsData
  )
    .filter(([, impl]) => langs.includes(impl.language))
    .filter(([key]) => !filteredReportImplementationsMap.has(key));
  return Object.fromEntries(filteredOtherImplementationsArray);
};

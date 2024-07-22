import { useMemo } from "react";

import CasesSection from "./components/Cases/CasesSection";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import Implementation from "./data/Implementation.ts";
import { ReportData } from "./data/parseReportData.ts";
import { FilterSection } from "./components/FilterSection.tsx";
import { useSearchParams } from "./hooks/useSearchParams.ts";

export const DialectReportView = ({
  reportData,
  topPageInfoSection,
  allImplementationsData,
}: {
  reportData: ReportData;
  topPageInfoSection?: React.ReactElement;
  allImplementationsData: Map<string, Implementation>;
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
        reportData.implementationsResults.entries(),
      ).filter(([id]) =>
        selectedLanguages.includes(
          reportData.runMetadata.implementations.get(id)!.language,
        ),
      );
      filteredData.implementationsResults = new Map(filteredReportArray);
    }

    return filteredData;
  }, [reportData, params]);

  const filteredOtherImplementationsData = useMemo(() => {
    const selectedLanguages = params.getAll("language");
    const availableLanguages =
      selectedLanguages.length > 0 ? selectedLanguages : languages;

    return new Map(
      Array.from(allImplementationsData)
        .filter(([, impl]) => availableLanguages.includes(impl.language))
        .filter(([key]) => !filteredReportData.implementationsResults.has(key)),
    );
  }, [params, allImplementationsData, languages, filteredReportData]);

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

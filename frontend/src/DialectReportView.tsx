import CasesSection from "./components/Cases/CasesSection";
import BowtieInfoSection from "./components/BowtieInfo/BowtieInfoSection";
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
import { OtherImplementations } from "./components/OtherImplementations.tsx";

export const DialectReportView = ({
  reportData,
  allImplementationsData,
}: {
  reportData: ReportData;
  allImplementationsData?: Implementation[];
}) => {
  const params = useSearchParams();

  const languages = useMemo(() => {
    const langs = Array.from(reportData.implementations.values()).map(
      (impl) => impl.metadata.language,
    );
    return Array.from(new Set(langs).values());
  }, [reportData]);

  const filteredData = useMemo(() => {
    const filteredReportData = { ...reportData };
    let filteredOtherImplementationsData: Implementation[] = [];
    const selectedLanguages = params.getAll("language");

    if (selectedLanguages.length > 0) {
      const filteredReportArray = Array.from(
        reportData.implementations.entries(),
      ).filter(([, data]) =>
        selectedLanguages.includes(data.metadata.language),
      );
      const filteredReportImplementationsMap = new Map(filteredReportArray);
      filteredReportData.implementations = filteredReportImplementationsMap;
      if (allImplementationsData) {
        filteredOtherImplementationsData = filterOtherImplementations(
          allImplementationsData,
          selectedLanguages,
          filteredReportImplementationsMap
        );
      }
    } else {
      const filteredReportArray = Array.from(
        reportData.implementations.entries(),
      );
      const filteredReportImplementationsMap = new Map(filteredReportArray);
      if (allImplementationsData) {
        filteredOtherImplementationsData = filterOtherImplementations(
          allImplementationsData,
          languages,
          filteredReportImplementationsMap
        );
      }
    }
    return { filteredReportData, filteredOtherImplementationsData };
  }, [reportData, params, allImplementationsData, languages]);

  return (
    <div>
      <div className="container p-4">
        <BowtieInfoSection />
        <RunInfoSection runInfo={filteredData.filteredReportData.runInfo} />
        <FilterSection languages={languages} />
        <SummarySection reportData={filteredData.filteredReportData} />
        {filteredData.filteredOtherImplementationsData.length > 0 && (
          <OtherImplementations
            otherImplementationsData={
              filteredData.filteredOtherImplementationsData
            }
          />
        )}
        <CasesSection reportData={filteredData.filteredReportData} />
      </div>
    </div>
  );
};

const filterOtherImplementations = (
  allImplementationsData: Implementation[],
  langs: string[],
  filteredReportImplementationsMap: Map<string, ImplementationData>,
) => {
  const filteredOtherImplementationsArray: Implementation[] =
    allImplementationsData.filter((impl: Implementation) =>
      langs.includes(impl.language),
    );
  const filteredOtherImplementationsData =
    filteredOtherImplementationsArray.filter((impl: Implementation) => {
      for (const val of filteredReportImplementationsMap.values()) {
        if (impl.source === val.metadata.source) {
          return false;
        }
      }
      return true;
    });
  return filteredOtherImplementationsData;
};

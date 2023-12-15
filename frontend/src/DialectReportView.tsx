// @ts-ignore
import CasesSection from "./components/Cases/CasesSection";
// @ts-ignore
import RunInfoSection from "./components/RunInfo/RunInfoSection";
// @ts-ignore
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

  const languages = useMemo(() => {
    const langs = Array.from(reportData.implementations.values()).map(
      (impl) => impl.metadata.language
    );
    return Array.from(new Set(langs).values());
  }, [reportData]);

  const registries = Array.from(reportData.cases.values()).filter(
    (value) => value.registry && value.registry.$vocabulary
  );
  const vocabularies = useMemo(() => {
    const registries = Array.from(reportData.cases.values()).filter(
      (value) => value.registry
    )
    const regs = Object.values(registries.map((reg) => reg.registry)[0]).filter(
      (reg) => reg.$vocabulary
    );

    const vocabs = regs.map((vocab) => {
      let arr = Object.keys(vocab.$vocabulary);
      return arr.map(val => val.split("/").pop());
    });
    return Array.from(new Set([].concat(...vocabs)).values());
  }, [reportData]);

  console.log(vocabularies);
  const filteredData = useMemo(() => {
    let filteredData = reportData;
    if (params.getAll("language").length) {
      const filteredArray = Array.from(
        reportData.implementations.entries()
      ).filter(([, data]) =>
        params.getAll("language").includes(data.metadata.language)
      );
      filteredData = { ...reportData, implementations: new Map(filteredArray) };
    }
    return filteredData;
  }, [reportData, params]);

  return (
    <div>
      <div className="container p-4">
        <RunInfoSection runInfo={filteredData.runInfo} />
        <FilterSection languages={languages} />
        <SummarySection reportData={filteredData} />
        <CasesSection reportData={filteredData} />
      </div>
    </div>
  );
};

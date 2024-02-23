import { useLoaderData } from "react-router-dom";
import { DialectReportView } from "./DialectReportView";
import { useContext, useEffect } from "react";
import { BowtieVersionContext } from "./context/BowtieVersionContext";
import { Implementation, ReportData } from "./data/parseReportData";

const ReportDataHandler = () => {
  const { setVersion } = useContext(BowtieVersionContext);
  const [report, prevImplementations] = useLoaderData() as [
    ReportData,
    Record<string, Implementation> | null,
  ];

  useEffect(
    () => setVersion!(report.runInfo.bowtie_version),
    [setVersion, report.runInfo.bowtie_version],
  );

  return (
    <DialectReportView
      reportData={report}
      prevImplementations={prevImplementations}
    />
  );
};

export default ReportDataHandler;

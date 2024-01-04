import { useLoaderData } from "react-router-dom";
import { DialectReportView } from "./DialectReportView";
import { useContext, useEffect } from "react";
import { BowtieVersionContext } from "./context/BowtieVersionContext";
import { ReportData } from "./data/parseReportData";

const ReportDataHandler = () => {
  const { setVersion } = useContext(BowtieVersionContext);
  const loaderData: ReportData = useLoaderData() as ReportData;

  useEffect(
    () => setVersion!(loaderData.runInfo.bowtie_version),
    [setVersion, loaderData.runInfo.bowtie_version],
  );

  return <DialectReportView reportData={loaderData} />;
};

export default ReportDataHandler;

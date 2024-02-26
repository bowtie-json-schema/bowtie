import { useLoaderData } from "react-router-dom";
import { DialectReportView } from "./DialectReportView";
import { useContext, useEffect } from "react";
import { BowtieVersionContext } from "./context/BowtieVersionContext";
import { ReportData } from "./data/parseReportData";
import BowtieInfoSection from "./components/BowtieInfo/BowtieInfoSection";

const ReportDataHandler = () => {
  const { setVersion } = useContext(BowtieVersionContext);
  const loaderData: ReportData = useLoaderData() as ReportData;

  useEffect(
    () => setVersion!(loaderData.runInfo.bowtie_version),
    [setVersion, loaderData.runInfo.bowtie_version],
  );

  return <DialectReportView reportData={loaderData} topPageInfoSection={<BowtieInfoSection />} />;
};

export default ReportDataHandler;

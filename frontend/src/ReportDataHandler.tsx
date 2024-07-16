import { useContext, useEffect } from "react";
import { useLoaderData } from "react-router-dom";

import { BowtieVersionContext } from "./context/BowtieVersionContext";
import BowtieInfoSection from "./components/BowtieInfo/BowtieInfoSection";
import { ReportData } from "./data/parseReportData";
import Implementation from "./data/Implementation";
import { DialectReportView } from "./DialectReportView";

interface LoaderData {
  reportData: ReportData;
  allImplementationsMetadata: Record<string, Implementation>;
}

const ReportDataHandler = () => {
  const { setVersion } = useContext(BowtieVersionContext);
  const loaderData: LoaderData = useLoaderData() as LoaderData;

  useEffect(
    () => setVersion!(loaderData.reportData.runMetadata.bowtieVersion),
    [setVersion, loaderData.reportData.runMetadata.bowtieVersion],
  );

  return (
    <DialectReportView
      reportData={loaderData.reportData}
      topPageInfoSection={<BowtieInfoSection />}
      allImplementationsMetadata={loaderData.allImplementationsMetadata}
    />
  );
};

export default ReportDataHandler;

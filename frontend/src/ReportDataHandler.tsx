import { useLoaderData } from "react-router-dom";
import { DialectReportView } from "./DialectReportView";
import { useContext, useEffect } from "react";
import { BowtieVersionContext } from "./context/BowtieVersionContext";
import { Implementation, ReportData } from "./data/parseReportData";
import BowtieInfoSection from "./components/BowtieInfo/BowtieInfoSection";

interface LoaderData {
  reportData: ReportData;
  allImplementationsData: Record<string, Implementation>;
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
      allImplementationsData={loaderData.allImplementationsData}
    />
  );
};

export default ReportDataHandler;

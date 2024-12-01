import { useContext, useEffect } from "react";
import { useLoaderData } from "react-router";

import BowtieInfoSection from "./components/BowtieInfo/BowtieInfoSection";
import Implementation from "./data/Implementation";
import { ReportData } from "./data/parseReportData";
import { BowtieVersionContext } from "./context/BowtieVersionContext";
import { DialectReportView } from "./DialectReportView";

interface LoaderData {
  reportData: ReportData;
  allImplementationsData: Map<string, Implementation>;
}

const DialectReportViewDataHandler = () => {
  const { setVersion } = useContext(BowtieVersionContext);
  const loaderData: LoaderData = useLoaderData();

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

export default DialectReportViewDataHandler;

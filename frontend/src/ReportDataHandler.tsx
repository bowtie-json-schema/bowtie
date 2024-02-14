import { useLoaderData } from "react-router-dom";
import { DialectReportView } from "./DialectReportView";
import { useContext, useEffect } from "react";
import { BowtieVersionContext } from "./context/BowtieVersionContext";
import { Implementation, ReportData } from "./data/parseReportData";

interface LoaderData {
  reportData: ReportData;
  allImplementationsData: Implementation[];
}

const ReportDataHandler = () => {
  const { setVersion } = useContext(BowtieVersionContext);
  const loaderData: LoaderData = useLoaderData() as LoaderData;

  useEffect(
    () => setVersion!(loaderData.reportData.runInfo.bowtie_version),
    [setVersion, loaderData.reportData.runInfo.bowtie_version]
  );

  return (
    <DialectReportView
      reportData={loaderData.reportData}
      allImplementationsData={loaderData.allImplementationsData}
    />
  );
};

export default ReportDataHandler;

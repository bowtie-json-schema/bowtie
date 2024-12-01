import { useContext, useEffect } from "react";
import { useLoaderData } from "react-router";

import BowtieInfoSection from "./components/BowtieInfo/BowtieInfoSection";
import Implementation from "./data/Implementation";
import { BowtieVersionContext } from "./context/BowtieVersionContext";
import { BenchmarkReportData } from "./data/parseBenchmarkData";
import { BenchmarkReportView } from "./BenchmarkReportView";

interface LoaderData {
  benchmarkReportData: BenchmarkReportData;
  allImplementationsData: Map<string, Implementation>;
}

const BenchmarkReportViewDataHandler = () => {
  const { setVersion } = useContext(BowtieVersionContext);
  const loaderData: LoaderData = useLoaderData();

  useEffect(
    () => setVersion!(loaderData.benchmarkReportData.metadata.bowtieVersion),
    [setVersion, loaderData.benchmarkReportData.metadata.bowtieVersion],
  );

  return (
    <BenchmarkReportView
      benchmarkReportData={loaderData.benchmarkReportData}
      topPageInfoSection={<BowtieInfoSection />}
    />
  );
};

export default BenchmarkReportViewDataHandler;

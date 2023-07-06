import { useLoaderData } from "react-router-dom";
import { ReportView } from "./ReportView";
import { useContext, useEffect } from "react";
import { BowtieVersionContext } from "./context/BowtieVersionContext";

const ReportDataHandler = () => {
  const { setVersion } = useContext(BowtieVersionContext);
  const loaderData = useLoaderData();

  useEffect(
    () => setVersion(loaderData.runInfo.bowtie_version),
    [setVersion, loaderData.runInfo.bowtie_version],
  );

  return <ReportView reportData={loaderData} />;
};

export default ReportDataHandler;

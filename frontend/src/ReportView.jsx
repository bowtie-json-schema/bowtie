import CasesSection from "./components/Cases/CasesSection";
import { RunTimeInfoModal } from "./components/Modals/RunTimeInfoModal";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import { RunInfo } from "./data/runInfo";
import { DetailsButtonModal } from "./components/Modals/DetailsButtonModal";
import { useContext, useEffect } from "react";
import { BowtieVersionContext } from "./context/BowtieVersionContext";

export const ReportView = ({ lines }) => {
  const { setVersion } = useContext(BowtieVersionContext);

  const runInfo = new RunInfo(lines);
  const summary = runInfo.createSummary();

  useEffect(
    () => setVersion(runInfo.bowtieVersion),
    [setVersion, runInfo.bowtieVersion],
  );

  return (
    <div>
      <div className="container p-4">
        <RunInfoSection runInfo={runInfo} />
        <SummarySection lines={lines} />
        <CasesSection lines={lines} />
      </div>
      <RunTimeInfoModal lines={lines} summary={summary} />
      <DetailsButtonModal lines={lines} summary={summary} />
    </div>
  );
};

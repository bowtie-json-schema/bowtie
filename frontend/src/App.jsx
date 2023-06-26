import CasesSection from "./components/Cases/CasesSection";
import { RunTimeInfoModal } from "./components/Modals/RunTimeInfoModal";
import NavBar from "./components/NavBar";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import { RunInfo } from "./data/runInfo";
import { DetailsButtonModal } from "./components/Modals/DetailsButtonModal";

function App({ lines }) {
  const runInfo = new RunInfo(lines);
  const summary = runInfo.createSummary();

  return (
    <div>
      <div>
        <NavBar runInfo={runInfo} />
        <div className="container p-4">
          <RunInfoSection runInfo={runInfo} />
          <SummarySection lines={lines} />
          <CasesSection lines={lines} />
        </div>
      </div>
      <RunTimeInfoModal lines={lines} summary={summary} />
      <DetailsButtonModal lines={lines} summary={summary} />
    </div>
  );
}
export default App;

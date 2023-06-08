import CasesSection from "./components/Cases/CasesSection";
import { RunTimeInfoModal } from "./components/Modals/RunTimeInfoModal";
import NavBar from "./components/NavBar";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import { RunInfo } from "./data/runInfo";
import { DetailsButtonModal } from "./components/Modals/DetailsButtonModal";

function App(props) {
  const runInfo = new RunInfo(props.lines);

  const summary = runInfo.createSummary();

  document.getElementsByTagName("title")[0].textContent +=
    " " + runInfo.dialect_shortname;

  return (
    <div>
      <NavBar runInfo={runInfo} />

      <div className="container p-4">
        <RunInfoSection runInfo={runInfo} />
        <SummarySection lines={props.lines} />
        <CasesSection lines={props.lines} />
      </div>
      <RunTimeInfoModal lines={props.lines} summary={summary} />
      <DetailsButtonModal lines={props.lines} summary={summary} />
    </div>
  );
}

export default App;

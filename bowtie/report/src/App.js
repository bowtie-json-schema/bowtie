import CasesSection from "./components/CasesSection";
import { RunTimeInfoModal } from "./components/Modals";
import NavBar from "./components/NavBar";
import RunInfoSection from "./components/RunInfoSection";
import SummarySection from "./components/SummarySection";
import { CountsDataProvider } from "./data/CountsDataContext";
import { RunInfo } from "./data/run-Info";

function App(props) {
  const runInfo = new RunInfo(props.lines);

  const summary = runInfo.create_summary();

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
    </div>
  );
}

export default App;

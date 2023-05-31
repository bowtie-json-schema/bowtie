import NavBar from "./components/NavBar";
import RunInfoSection from "./components/RunInfoSection";
import SummarySection from "./components/SummarySection";
import { RunInfo } from "./data/run-Info";

function App(props) {
  const runInfo = new RunInfo(props.lines[0]);

  const summary = runInfo.create_summary();

  document.getElementsByTagName("title")[0].textContent += ' ' +
    runInfo.dialect_shortname;

  return (
    <div>
      <NavBar runInfo={runInfo} />

      <div className="container p-4">
        <RunInfoSection runInfo={runInfo} />
        <SummarySection summary={summary} />
      </div>

    </div>
  );
}

export default App;

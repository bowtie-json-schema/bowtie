import NavBar from "./components/NavBar";
import RunInfoSection from "./components/RunInfoSection";
import { RunInfo } from "./data/run-Info";

function App(props) {
  const runInfo = new RunInfo(props.lines[0]);
  // console.log(runInfo)
  document.getElementsByTagName("title")[0].textContent += ' ' + 
    runInfo.dialect_shortname;

  return (
    <div>

      <NavBar runInfo={runInfo} />

      <div className="container p-4">
        <RunInfoSection runInfo={runInfo} />
      </div>

    </div>
  );
}

export default App;

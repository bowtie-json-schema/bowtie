import NavBar from "./components/NavBar";
import { RunInfo } from "./data/run-Info";

function App(props) {
  const runInfo = new RunInfo(props.lines[0]);
  // console.log(runInfo)
  document.getElementsByTagName('title')[0].textContent += runInfo.dialect_shortname;
  
  return (
    <div>
      <NavBar runInfo={runInfo} />
      </div>
  );
}

export default App;

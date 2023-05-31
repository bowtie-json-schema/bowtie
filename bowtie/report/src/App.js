import NavBar from "./components/NavBar";
import { RunInfo } from "./data/run-Info";

function App(props) {
  const runInfo = new RunInfo(props.lines[0]);
  // console.log(runInfo)
  
  return (
    <div>
      <NavBar runInfo={runInfo} />
      </div>
  );
}

export default App;

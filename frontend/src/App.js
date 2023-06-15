import CasesSection from "./components/Cases/CasesSection";
import { RunTimeInfoModal } from "./components/Modals/RunTimeInfoModal";
import NavBar from "./components/NavBar";
import RunInfoSection from "./components/RunInfo/RunInfoSection";
import SummarySection from "./components/Summary/SummarySection";
import { RunInfo } from "./data/runInfo";
import { DetailsButtonModal } from "./components/Modals/DetailsButtonModal";
import DragAndDrop from "./components/DragAndDrop/DragAndDrop";
import { useEffect, useState } from "react";

function App({ draftName }) {
  if (draftName !== "local-report") {
    const [lines, setLines] = useState([]);
    useEffect(() => {
      document.getElementsByTagName("title")[0].textContent += " " + draftName;
      fetch(`https://bowtie-json-schema.github.io/bowtie/${draftName}.jsonl`)
        .then((response) => response.text())
        .then((jsonl) => {
          const dataObjectsArray = jsonl.trim().split(/\n(?=\{)/);
          setLines(dataObjectsArray.map((line) => JSON.parse(line)));
        });
    }, [draftName]);

    if (!lines.length) {
      return null;
    }

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
  } else {
    document.getElementsByTagName("title")[0].textContent += " " + draftName;
    return <DragAndDrop />;
  }
}

export default App;

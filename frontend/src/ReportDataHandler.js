import { RunInfo } from "./data/runInfo";
import { useState, useEffect } from "react";
import App from "./App";

const ReportDataHandler = ({ draftName }) => {
  const [report, setReport] = useState("local");
  const [lines, setLines] = useState([]);
  useEffect(() => {
    if (draftName !== "local-report") {
      setReport("remote");
    }
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
    <>
      {report === "local" ? (
        <>
          {(document.title += " " + draftName)}
          <DragAndDrop />
        </>
      ) : (
        <App lines={lines} />
      )}
    </>
  );
};

export default ReportDataHandler;

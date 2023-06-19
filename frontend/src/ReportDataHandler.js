import { useState, useEffect } from "react";
import App from "./App";
import DragAndDrop from "./components/DragAndDrop/DragAndDrop";

const ReportDataHandler = ({ draftName }) => {
  let [report, setReport] = useState("local");
  const [lines, setLines] = useState([]);
  useEffect(() => {
    if (draftName !== "local-report") {
      setReport("remote");
      document.getElementsByTagName("title")[0].textContent =
        " Bowtie-" + draftName;
      fetch(`https://bowtie-json-schema.github.io/bowtie/${draftName}.jsonl`)
        .then((response) => response.text())
        .then((jsonl) => {
          const dataObjectsArray = jsonl.trim().split(/\n(?=\{)/);
          setLines(dataObjectsArray.map((line) => JSON.parse(line)));
        });
    } else {
      setReport("local");
    }
  }, [draftName]);

  if (!lines.length) {
    return null;
  }
  console.log(report);

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

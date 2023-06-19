import { useState, useEffect } from "react";
import App from "./App";

const ReportDataHandler = ({ draftName }) => {
  const [lines, setLines] = useState([]);
  useEffect(() => {
    document.getElementsByTagName("title")[0].textContent =
      " Bowtie-" + draftName;
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

  return <App lines={lines} />;
};

export default ReportDataHandler;

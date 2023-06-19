import { useState, useEffect } from "react";
import App from "./App";
import NavBar from "./components/NavBar";
import { RunInfo } from "./data/runInfo";
import LoadingAnimation from "./components/LoadingAnimation";

const ReportDataHandler = ({ draftName }) => {
  const [lines, setLines] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    document.getElementsByTagName("title")[0].textContent =
      " Bowtie-" + draftName;
    setIsLoading(true);
    fetch(`https://bowtie-json-schema.github.io/bowtie/${draftName}.jsonl`)
      .then((response) => response.text())
      .then((jsonl) => {
        const dataObjectsArray = jsonl.trim().split(/\n(?=\{)/);
        setLines(dataObjectsArray.map((line) => JSON.parse(line)));
        setIsLoading(false);
      });
  }, [draftName]);

  return (
    <>
      {isLoading ? (
        <>
          <NavBar /> <LoadingAnimation />
        </>
      ) : (
        <App lines={lines} />
      )}
    </>
  );
};

export default ReportDataHandler;

import { createRoot } from "react-dom/client";
import App from "./App";
import { CountsDataProvider } from "./data/CountsDataContext";

document.addEventListener("DOMContentLoaded", () => {
  const Dialect = "2020-12";

  //fetching json data from url
  fetch(`https://bowtie-json-schema.github.io/bowtie/draft${Dialect}.json.gz`)
    .then((response) => response.arrayBuffer())
    .then((buffer) => {
      const inflated = pako.inflate(buffer, { to: "string" });
      const dataObjectsArray = inflated.trim().split(/\n(?=\{)/);
      // console.log(inflated)
      const lines = dataObjectsArray.map((line) => JSON.parse(line));

      const root = createRoot(document.getElementById("root"));

      root.render(
        <CountsDataProvider>
          <App lines={lines} />
        </CountsDataProvider>
      );
    });
});

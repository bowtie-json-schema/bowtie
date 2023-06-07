import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import pako from "pako";

import { createRoot } from "react-dom/client";
import App from "./App";

document.addEventListener("DOMContentLoaded", () => {
  let Dialect = "2020-12";
  let dialect;

  const url = window.location.href;
  const urlParts = url.split("/");
  let draftPart;
  for (const part of urlParts) {
    if (part.includes("draft")) {
      draftPart = part;
      break;
    }
  }
  if (draftPart) {
    dialect = draftPart.substring(draftPart.indexOf("draft") + "draft".length);
  }

  switch (dialect) {
    case "2020-12":
    case "2019-09":
    case "7":
    case "6":
    case "4":
    case "3":
      Dialect = dialect;
      break;
  }

  //fetching json data from url
  fetch(`https://bowtie-json-schema.github.io/bowtie/draft${Dialect}.json.gz`)
    .then((response) => response.arrayBuffer())
    .then((buffer) => {
      const inflated = pako.inflate(buffer, { to: "string" });
      const dataObjectsArray = inflated.trim().split(/\n(?=\{)/);
      // console.log(inflated)
      const lines = dataObjectsArray.map((line) => JSON.parse(line));

      const root = createRoot(document.getElementById("root"));

      root.render(<App lines={lines} />);
    });
});

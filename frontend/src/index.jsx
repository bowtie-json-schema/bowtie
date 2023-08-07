import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import { createRoot } from "react-dom/client";
import ReportDataHandler from "./ReportDataHandler";
import { createHashRouter, RouterProvider } from "react-router-dom";
import ThemeContextProvider from "./context/ThemeContext";
import { MainContainer } from "./MainContainer";
import { BowtieVersionContextProvider } from "./context/BowtieVersionContext";
import { DragAndDrop } from "./components/DragAndDrop/DragAndDrop";
import { parseReportData } from "./data/parseReportData";
import { PerImplementationPage } from "./components/Per-ImplementationPage/PerImplementationPage";

const reportUrl = "https://bowtie.report";
const titleTag = document.getElementsByTagName("title")[0];
const dialectToName = {
  "draft2020-12": "Draft 2020-12",
  "draft2019-09": "Draft 2019-09",
  draft7: "Draft 7",
  draft6: "Draft 6",
  draft4: "Draft 4",
  draft3: "Draft 3",
};

const fetchReportData = async (dialect, implementation) => {
  const dialectName = dialectToName[dialect] || dialect;
  titleTag.textContent = `Bowtie - ${dialectName}`;
  const response = await fetch(`${reportUrl}/${dialect}.json`);
  const jsonl = await response.text();
  const lines = jsonl.trim().split(/\r?\n/).map(JSON.parse);

  if (implementation) {
    const filteredData = lines.filter(
      (obj) =>
        !obj.implementation || obj.implementation.includes(implementation)
    );
    for (const key in filteredData[0]?.implementations) {
      if (!key.includes(implementation)) {
        delete filteredData[0].implementations[key];
      }
    }
    return parseReportData(filteredData);
  }

  return parseReportData(lines);
};

const implementations = [
  "clojure-json-schema",
  "cpp-valijson",
  "dotnet-jsonschema-net",
  "go-gojsonschema",
  "go-jsonschema",
  "java-json-schema",
  "java-json-schema-validator",
  "js-ajv",
  "js-hyperjump",
  "lua-josnschema",
  "python-fastjsonschema",
  "python-jschon",
  "python-jsonschema",
  "ruby-json_schemer",
  "rust-boon",
  "rust-jsonschema",
  "ts-vscode-json-languageservice",
];

const router = createHashRouter([
  {
    path: "/",
    Component: MainContainer,

    children: [
      {
        index: true,
        Component: ReportDataHandler,
        loader: async () => fetchReportData("draft2020-12"),
      },
      {
        path: "/:draftName",
        Component: ReportDataHandler,
        loader: async ({ params }) => fetchReportData(params.draftName),
      },
      {
        path: "/local-report",
        Component: DragAndDrop,
      },
      {
        path: "/implementations/:langImplementation/dialects/:dialectName",
        Component: PerImplementationPage,
        loader: async ({ params }) =>
          fetchReportData(params.dialectName, params.langImplementation),
      },
      {
        path: "/docs",
        Component: () => {
          window.location.href =
            "https://bowtie-json-schema.readthedocs.io/en/latest/";
          return null;
        },
      },
    ],
  },
]);

document.addEventListener("DOMContentLoaded", () => {
  const root = createRoot(document.getElementById("root"));
  root.render(
    <ThemeContextProvider>
      <BowtieVersionContextProvider>
        <RouterProvider router={router} />
      </BowtieVersionContextProvider>
    </ThemeContextProvider>
  );
});

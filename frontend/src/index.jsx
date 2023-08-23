import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import { createRoot } from "react-dom/client";
import ReportDataHandler from "./ReportDataHandler";
import { createHashRouter, RouterProvider } from "react-router-dom";
import ThemeContextProvider from "./context/ThemeContext";
import { MainContainer } from "./MainContainer";
import { BowtieVersionContextProvider } from "./context/BowtieVersionContext";
import { DragAndDrop } from "./components/DragAndDrop/DragAndDrop";
import { Dialect } from "./data/Dialect";
import {
  parseReportData,
  parseImplementationData,
} from "./data/parseReportData";
import URI from "urijs";
import { ImplementationReportView } from "./components/ImplementationReportView/ImplementationReportView";

const reportHost =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;
const reportUri = new URI(reportHost).directory(import.meta.env.BASE_URL);

const fetchReportData = async (dialect) => {
  const dialectName = Dialect.dialectToName[dialect] ?? dialect;
  document.title = `Bowtie - ${dialectName}`;
  const url = reportUri.clone().filename(dialect).suffix("json").href();
  const response = await fetch(url);
  const jsonl = await response.text();
  const lines = jsonl
    .trim()
    .split(/\r?\n/)
    .map((line) => JSON.parse(line));
  return parseReportData(lines);
};

const fetchAllReportData = async () => {
  const loaderData = {};
  const fetchPromises = Object.keys(Dialect.dialectToName).map(
    async (dialect) => (loaderData[dialect] = await fetchReportData(dialect)),
  );
  await Promise.all(fetchPromises);
  return parseImplementationData(loaderData);
};

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
        path: "/dialects/:draftName",
        Component: ReportDataHandler,
        loader: async ({ params }) => fetchReportData(params.draftName),
      },
      {
        path: "/local-report",
        Component: DragAndDrop,
      },
      {
        path: "/implementations/:langImplementation",
        Component: ImplementationReportView,
        loader: fetchAllReportData,
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
    </ThemeContextProvider>,
  );
});

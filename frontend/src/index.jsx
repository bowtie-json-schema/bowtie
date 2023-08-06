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

const getReportUrl = () => {
  return import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : import.meta.env.BASE_URL;
};

const removeTrailingSlash = (path) => path.replace(/\/$/, "");

const reportUrl = removeTrailingSlash(getReportUrl());
const titleTag = document.getElementsByTagName("title")[0];
const dialectToName = {
  "draft2020-12": "Draft 2020-12",
  "draft2019-09": "Draft 2019-09",
  draft7: "Draft 7",
  draft6: "Draft 6",
  draft4: "Draft 4",
  draft3: "Draft 3",
};

const fetchReportData = async (dialect) => {
  const dialectName = dialectToName[dialect] ?? dialect;
  titleTag.textContent = `Bowtie - ${dialectName}`;
  const response = await fetch(`${reportUrl}/${dialect}.json`);
  const jsonl = await response.text();
  const lines = jsonl
    .trim()
    .split(/\r?\n/)
    .map((line) => JSON.parse(line));
  return parseReportData(lines);
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
        path: "/:draftName",
        Component: ReportDataHandler,
        loader: async ({ params }) => fetchReportData(params.draftName),
      },
      {
        path: "/local-report",
        Component: DragAndDrop,
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

import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import { createRoot } from "react-dom/client";
import ReportDataHandler from "./ReportDataHandler";
import { createHashRouter, RouterProvider } from "react-router-dom";
import ThemeContextProvider from "./context/ThemeContext";
import { MainContainer } from "./MainContainer";
import { BowtieVersionContextProvider } from "./context/BowtieVersionContext";
import { DragAndDrop } from "./components/DragAndDrop/DragAndDrop";

const reportUrl =
  import.meta.env.MODE === "development"
    ? "https://bowtie-json-schema.github.io/bowtie"
    : import.meta.env.BASE_URL;
const titleTag = document.getElementsByTagName("title")[0];

const fetchReportData = async (dialect) => {
  titleTag.textContent = `Bowtie - ${dialect}`;
  const response = await fetch(`${reportUrl}/${dialect}.json`);
  const jsonl = await response.text();
  return jsonl
    .trim()
    .split(/\r?\n/)
    .map((line) => JSON.parse(line));
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
    ]
  }
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

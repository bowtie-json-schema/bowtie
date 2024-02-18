import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import { createRoot } from "react-dom/client";
import ReportDataHandler from "./ReportDataHandler";
import { createHashRouter, Navigate, RouterProvider } from "react-router-dom";
import ThemeContextProvider from "./context/ThemeContext";
import { MainContainer } from "./MainContainer";
import { BowtieVersionContextProvider } from "./context/BowtieVersionContext";
import { DragAndDrop } from "./components/DragAndDrop/DragAndDrop";
import Dialect from "./data/Dialect";
import { parseImplementationData, ReportData } from "./data/parseReportData";
import URI from "urijs";
import { ImplementationReportView } from "./components/ImplementationReportView/ImplementationReportView";

const reportHost =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;
const reportUri = new URI(reportHost).directory(import.meta.env.BASE_URL);

const fetchReportData = async (dialect: Dialect) => {
  document.title = `Bowtie - ${dialect.prettyName}`;
  return dialect.fetchReport(reportUri);
};

const fetchAllReportData = async (langImplementation: string) => {
  document.title = `Bowtie - ${langImplementation}`;
  const loaderData: Record<string, ReportData> = {};
  const promises = [];
  for (const dialect of Dialect.known()) {
    promises.push(
      dialect
        .fetchReport(reportUri)
        .then((data) => (loaderData[dialect.path] = data)),
    );
  }
  await Promise.all(promises);
  return parseImplementationData(loaderData);
};

const router = createHashRouter([
  {
    path: "/",
    Component: MainContainer,

    children: [
      {
        index: true,
        element: <Navigate to="/dialects/draft2020-12" replace />,
      },
      {
        path: "/dialects/:draftName",
        Component: ReportDataHandler,
        loader: async ({ params }) =>
          fetchReportData(Dialect.forPath(params.draftName!)),
      },
      {
        path: "/local-report",
        Component: DragAndDrop,
      },
      {
        path: "/implementations/:langImplementation",
        Component: ImplementationReportView,
        loader: async ({ params }) =>
          fetchAllReportData(params.langImplementation!),
      },
    ],
  },
]);

document.addEventListener("DOMContentLoaded", () => {
  const root = createRoot(document.getElementById("root")!);
  root.render(
    <ThemeContextProvider>
      <BowtieVersionContextProvider>
        <RouterProvider router={router} />
      </BowtieVersionContextProvider>
    </ThemeContextProvider>,
  );
});

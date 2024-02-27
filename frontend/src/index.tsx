import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import { createRoot } from "react-dom/client";
import ReportDataHandler from "./ReportDataHandler";
import { createHashRouter, Params, RouterProvider } from "react-router-dom";
import ThemeContextProvider from "./context/ThemeContext";
import { MainContainer } from "./MainContainer";
import { BowtieVersionContextProvider } from "./context/BowtieVersionContext";
import { DragAndDrop } from "./components/DragAndDrop/DragAndDrop";
import { ImplementationReportView } from "./components/ImplementationReportView/ImplementationReportView";
import Dialect from "./data/Dialect";
import { implementationMetadataURI } from "./data/Site";
import {
  Implementation,
  parseImplementationData,
  ReportData,
} from "./data/parseReportData";

const fetchReportData = async (dialect: Dialect) => {
  document.title = `Bowtie - ${dialect.prettyName}`;
  return dialect.fetchReport();
};

const fetchAllReportData = async (langImplementation: string) => {
  document.title = `Bowtie - ${langImplementation}`;
  const loaderData: Record<string, ReportData> = {};
  const promises = [];
  for (const dialect of Dialect.known()) {
    promises.push(
      dialect
        .fetchReport()
        .then((data) => (loaderData[dialect.shortName] = data)),
    );
  }
  await Promise.all(promises);
  return parseImplementationData(loaderData);
};

const fetchImplementationMetadata = async () => {
  const response = await fetch(implementationMetadataURI);
  const implementations = (await response.json()) as Record<
    string,
    Implementation
  >;
  return implementations;
};

const reportDataLoader = async ({ params }: { params: Params<string> }) => {
  const draftName = params?.draftName ?? "draft2020-12";
  const [reportData, allImplementationsData] = await Promise.all([
    fetchReportData(Dialect.withName(draftName)),
    fetchImplementationMetadata(),
  ]);
  return { reportData, allImplementationsData };
};

const router = createHashRouter([
  {
    path: "/",
    Component: MainContainer,

    children: [
      {
        index: true,
        Component: ReportDataHandler,
        loader: reportDataLoader,
      },
      {
        path: "/dialects/:draftName",
        Component: ReportDataHandler,
        loader: reportDataLoader,
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

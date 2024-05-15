import "bootstrap/dist/css/bootstrap.min.css";
import { createHashRouter, Params, RouterProvider } from "react-router-dom";
import { createRoot } from "react-dom/client";

import "./global.css";
import Dialect from "./data/Dialect";
import ReportDataHandler from "./ReportDataHandler";
import ThemeContextProvider from "./context/ThemeContext";
import { BowtieVersionContextProvider } from "./context/BowtieVersionContext";
import { DragAndDrop } from "./components/DragAndDrop/DragAndDrop";
import { ImplementationReportView } from "./components/ImplementationReportView/ImplementationReportView";
import { MainContainer } from "./MainContainer";
import { implementationMetadataURI } from "./data/Site";
import {
  ImplementationData,
  ReportData,
  implementationFromData,
  prepareImplementationReport,
} from "./data/parseReportData";

const fetchReportData = async (dialect: Dialect) => {
  document.title = `Bowtie - ${dialect.prettyName}`;
  return dialect.fetchReport();
};

const fetchAllReportsData = async (langImplementation: string) => {
  document.title = `Bowtie - ${langImplementation}`;
  const allReportsData = new Map<Dialect, ReportData>();
  const promises = [];
  for (const dialect of Dialect.known()) {
    promises.push(
      dialect.fetchReport().then((data) => allReportsData.set(dialect, data)),
    );
  }
  await Promise.all(promises);
  return prepareImplementationReport(allReportsData, langImplementation);
};

const fetchImplementationMetadata = async () => {
  const response = await fetch(implementationMetadataURI);
  const implementations = (await response.json()) as Record<
    string,
    ImplementationData
  >;
  return Object.fromEntries(
    Object.entries(implementations).map(([id, data]) => [
      id,
      implementationFromData(data),
    ]),
  );
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
          fetchAllReportsData(params.langImplementation!),
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

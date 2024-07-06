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
import {
  ReportData,
  prepareImplementationReport,
} from "./data/parseReportData";
import EmbedBadges from "./components/ImplementationReportView/EmbedBadges";
import Implementation from "./data/Implementation";

const fetchReportData = async (dialect: Dialect) => {
  document.title = `Bowtie - ${dialect.prettyName}`;
  return dialect.fetchReport();
};

const fetchImplementationReportViewData = async (implementationId: string) => {
  document.title = `Bowtie - ${implementationId}`;
  const allReportsData = new Map<Dialect, ReportData>();
  const promises = [];
  for (const dialect of Dialect.known()) {
    promises.push(
      dialect.fetchReport().then((data) => allReportsData.set(dialect, data))
    );
  }
  await Promise.all(promises);
  return prepareImplementationReport(implementationId, allReportsData);
};

const fetchAllImplementationsMetadata = async () => {
  const rawImplementationsData =
    await Implementation.fetchAllImplementationsMetadata();
  return Object.fromEntries(
    Object.entries(rawImplementationsData).map(
      ([implementationId, rawImplementationData]) => [
        implementationId,
        new Implementation(implementationId, rawImplementationData),
      ]
    )
  );
};

const reportDataLoader = async ({ params }: { params: Params<string> }) => {
  const draftName = params?.draftName ?? "draft2020-12";
  const [reportData, allImplementationsMetadata] = await Promise.all([
    fetchReportData(Dialect.withName(draftName)),
    fetchAllImplementationsMetadata(),
  ]);
  return { reportData, allImplementationsMetadata };
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
        path: "/implementations/:implementationId",
        Component: ImplementationReportView,
        loader: async ({ params }) =>
          fetchImplementationReportViewData(params.implementationId!),
        children: [
          {
            path: "badges",
            Component: EmbedBadges,
          },
        ],
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
    </ThemeContextProvider>
  );
});

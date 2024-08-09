import "bootstrap/dist/css/bootstrap.min.css";
import "./global.css";
import { createRoot } from "react-dom/client";
import { createHashRouter, Params, RouterProvider } from "react-router-dom";

import Dialect from "./data/Dialect";
import DialectReportViewDataHandler from "./DialectReportViewDataHandler";
import ThemeContextProvider from "./context/ThemeContext";
import Implementation from "./data/Implementation";
import EmbedBadges from "./components/ImplementationReportView/EmbedBadges";
import { BowtieVersionContextProvider } from "./context/BowtieVersionContext";
import { DragAndDrop } from "./components/DragAndDrop/DragAndDrop";
import { ImplementationReportView } from "./components/ImplementationReportView/ImplementationReportView";
import { MainContainer } from "./MainContainer";
import {
  ReportData,
  prepareImplementationReport,
} from "./data/parseReportData";

const implementationReportViewDataLoader = async (
  langImplementation: string,
) => {
  document.title = `Bowtie - ${langImplementation}`;
  const allReportsData = new Map<Dialect, ReportData>();
  const promises = [];
  for (const dialect of Dialect.known()) {
    promises.push(
      dialect.fetchReport().then((data) => allReportsData.set(dialect, data)),
    );
  }
  await Promise.all(promises);
  return prepareImplementationReport(langImplementation, allReportsData);
};

const dialectReportViewDataLoader = async ({
  params,
}: {
  params: Params<string>;
}) => {
  const draftName = params?.draftName ?? "draft2020-12";
  const dialect = Dialect.withName(draftName);
  document.title = `Bowtie - ${dialect.prettyName}`;

  const [reportData, allImplementationsData] = await Promise.all([
    dialect.fetchReport(),
    Implementation.fetchAllImplementationsData(),
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
        Component: DialectReportViewDataHandler,
        loader: dialectReportViewDataLoader,
      },
      {
        path: "/dialects/:draftName",
        Component: DialectReportViewDataHandler,
        loader: dialectReportViewDataLoader,
      },
      {
        path: "/local-report",
        Component: DragAndDrop,
      },
      {
        path: "/implementations/:langImplementation",
        Component: ImplementationReportView,
        loader: async ({ params }) =>
          implementationReportViewDataLoader(params.langImplementation!),
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
    </ThemeContextProvider>,
  );
});

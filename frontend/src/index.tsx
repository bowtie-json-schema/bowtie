import "bootstrap/dist/css/bootstrap.min.css";
import "./global.css";
import { createRoot } from "react-dom/client";
import { createHashRouter, Params, RouterProvider } from "react-router";

import Dialect from "./data/Dialect";
import DialectReportViewDataHandler from "./DialectReportViewDataHandler";
import BenchmarkReportViewDataHandler from "./BenchmarkReportViewDataHandler";
import ThemeContextProvider from "./context/ThemeContext";
import Implementation from "./data/Implementation";
import EmbedBadges from "./components/ImplementationReportView/EmbedBadges";
import { BowtieVersionContextProvider } from "./context/BowtieVersionContext";
import { DragAndDrop } from "./components/DragAndDrop/DragAndDrop";
import { ImplementationReportView } from "./components/ImplementationReportView/ImplementationReportView";
import { MainContainer } from "./MainContainer";
import {
  ImplementationReport,
  prepareDialectsComplianceReportFor,
} from "./data/parseReportData";
import NotFound from "./components/NotFound";

const implementationReportViewDataLoader = async (implementationId: string) => {
  document.title = `Bowtie - ${implementationId}`;

  const allDialectReports = await Dialect.fetchAllReports();

  const implementation = Implementation.withId(implementationId);
  if (!implementation) return null;

  const dialectsCompliance = prepareDialectsComplianceReportFor(
    implementation.id,
    allDialectReports,
  );

  await implementation.fetchVersions();

  return {
    implementation,
    dialectsCompliance,
  } satisfies ImplementationReport;
};

const dialectReportViewDataLoader = async ({
  params,
}: {
  params: Params<string>;
}) => {
  const draftName = params?.draftName ?? Dialect.latest().shortName;
  const dialect = Dialect.withName(draftName);

  document.title = `Bowtie - ${dialect.prettyName}`;

  const [reportData, allImplementationsData] = await Promise.all([
    dialect.fetchReport(),
    Implementation.fetchAllImplementationsData(),
  ]);
  return { reportData, allImplementationsData };
};

const benchmarkReportViewDataLoader = async ({
  params,
}: {
  params: Params<string>;
}) => {
  const draftName = params?.draftName ?? Dialect.latest().shortName;
  const dialect = Dialect.withName(draftName);
  document.title = `Benchmarks - ${dialect.prettyName}`;

  const [benchmarkReportData, allImplementationsData] = await Promise.all([
    dialect.fetchBenchmarkReport(),
    Implementation.fetchAllImplementationsData(),
  ]);
  return { benchmarkReportData, allImplementationsData };
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
        path: "/benchmarks/",
        Component: BenchmarkReportViewDataHandler,
        loader: benchmarkReportViewDataLoader,
      },
      {
        path: "/benchmarks/:draftName",
        Component: BenchmarkReportViewDataHandler,
        loader: benchmarkReportViewDataLoader,
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
  {
    path: "*",
    Component: NotFound,
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

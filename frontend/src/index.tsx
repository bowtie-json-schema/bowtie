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
  ImplementationReport,
  prepareDialectsComplianceReport,
  prepareVersionsComplianceReport,
} from "./data/parseReportData";

const implementationReportViewDataLoader = async (implementationId: string) => {
  document.title = `Bowtie - ${implementationId}`;

  const allDialectReports = await Dialect.fetchAllReports();

  const implementation = Implementation.withId(implementationId);
  if (!implementation) return null;

  const versions = await implementation.fetchVersions();
  const versionedReports = await implementation.fetchVersionedReportsFor(
    versions,
    Dialect.newest_to_oldest()[0],
  );

  return {
    implementation,
    dialectsCompliance: prepareDialectsComplianceReport(
      implementation.id,
      allDialectReports,
    ),
    versionsCompliance: prepareVersionsComplianceReport(versionedReports),
  } satisfies ImplementationReport;
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

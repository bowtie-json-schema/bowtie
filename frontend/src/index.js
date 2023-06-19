import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import { createRoot } from "react-dom/client";
import ReportDataHandler from "./ReportDataHandler";
import { createHashRouter, RouterProvider } from "react-router-dom";
import DragAndDrop from "./components/DragAndDrop/DragAndDrop";

const router = createHashRouter([
  {
    path: "/",
    element: <DragAndDrop />,
  },
  {
    path: "/:draftName",
    element: <ReportDataHandler />,
    loader: ({ params }) => {
      document.getElementsByTagName("title")[0].textContent =
        " Bowtie-" + params.draftName;
      return fetch(
        `https://bowtie-json-schema.github.io/bowtie/${params.draftName}.jsonl`
      )
        .then((response) => response.text())
        .then((jsonl) => {
          const dataObjectsArray = jsonl.trim().split(/\n(?=\{)/);
          const lines = dataObjectsArray.map((line) => JSON.parse(line));
          return lines;
        });
    },
  },
]);

document.addEventListener("DOMContentLoaded", () => {
  const root = createRoot(document.getElementById("root"));
  root.render(<RouterProvider router={router} />);
});
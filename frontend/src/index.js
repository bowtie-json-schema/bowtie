import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import { createRoot } from "react-dom/client";
import ReportDataHandler from "./ReportDataHandler";
import { createHashRouter, RouterProvider } from "react-router-dom";
import DragAndDrop from "./components/DragAndDrop/DragAndDrop";
import ThemeContextProvider from "./context/ThemeContext";

const router = createHashRouter([
  {
    path: "/",
    element: <DragAndDrop />,
  },
  {
    path: "/:draftName",
    element: <ReportDataHandler />,
    loader: async ({ params }) => {
      document.getElementsByTagName("title")[0].textContent =
        " Bowtie-" + params.draftName;
      const response = await fetch(
        `${process.env.PUBLIC_URL}/${params.draftName}.json`,
        // FOR DEVELOPMENT PUROPOSE,COMMET THE ABOVE LINE AND UNCOMMENT THE BELOW LINE
        // `https://bowtie-json-schema.github.io/bowtie/${params.draftName}.json`
      );
      const jsonl = await response.text();
      const dataObjectsArray = jsonl.trim().split(/\r?\n/);
      const lines = dataObjectsArray.map((line) => JSON.parse(line));
      return lines;
    },
  },
]);

document.addEventListener("DOMContentLoaded", () => {
  const root = createRoot(document.getElementById("root"));
  root.render(
    <ThemeContextProvider>
      <RouterProvider router={router} />
    </ThemeContextProvider>,
  );
});

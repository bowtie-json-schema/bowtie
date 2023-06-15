import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import { createRoot } from "react-dom/client";
import App from "./App";
import { createHashRouter, RouterProvider } from "react-router-dom";

const router = createHashRouter([
  {
    path: "/",
    element: <App draftName="local-report" />,
  },
  {
    path: "/draft2020-12",
    element: <App draftName="draft2020-12" />,
  },
  {
    path: "/draft2019-09",
    element: <App draftName="draft2019-09" />,
  },
  {
    path: "/draft7",
    element: <App draftName="draft7" />,
  },
  {
    path: "/draft6",
    element: <App draftName="draft6" />,
  },
  {
    path: "/draft4",
    element: <App draftName="draft4" />,
  },
  {
    path: "/draft3",
    element: <App draftName="draft3" />,
  },
]);

document.addEventListener("DOMContentLoaded", () => {
  const root = createRoot(document.getElementById("root"));
  root.render(<RouterProvider router={router} />);
});

import { useState, useEffect } from "react";
import { useLoaderData } from "react-router";

import App from "./App";
import LoadingAnimation from "./components/LoadingAnimation";

const ReportDataHandler = () => {
  const [loading, setLoading] = useState(true);
  let [lines, setLines] = useState([]);
  const loaderData = useLoaderData("draftName");

  useEffect(() => {
    setLoading(true);
    setLines(loaderData);

    setLoading(false);
  }, [loaderData]);

  return <>{loading ? <LoadingAnimation /> : <App lines={lines} />}</>;
};

export default ReportDataHandler;

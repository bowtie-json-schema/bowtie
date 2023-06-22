import { useState, useEffect } from "react";
import { useLoaderData, useNavigation } from "react-router-dom";

import App from "./App";
import LoadingAnimation from "./components/LoadingAnimation";

const ReportDataHandler = () => {
  const [isLoading, setIsLoading] = useState(true);
  const loaderData = useLoaderData();
  const state = useNavigation().state === "loading";

  useEffect(() => {
    setIsLoading(!isLoading);
  }, [state]);

  return isLoading ? <LoadingAnimation /> : <App lines={loaderData} />;
};

export default ReportDataHandler;

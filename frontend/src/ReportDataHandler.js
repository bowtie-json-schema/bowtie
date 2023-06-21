import { useState, useEffect } from "react";
import { useLoaderData, useNavigation } from "react-router-dom";

import App from "./App";
import LoadingAnimation from "./components/LoadingAnimation";

const ReportDataHandler = () => {
  const [isLoading, setIsLoading] = useState(true);
  const loaderData = useLoaderData();

  useEffect(() => {
    setIsLoading(!isLoading);
  }, [useNavigation().state === "loading"]);

  return isLoading ? <LoadingAnimation /> : <App lines={loaderData} />;
};

export default ReportDataHandler;

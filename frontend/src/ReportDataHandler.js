import { useState, useEffect } from "react";
import { useLoaderData } from "react-router";

import App from "./App";
import LoadingAnimation from "./components/LoadingAnimation";

const ReportDataHandler = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const loaderData = useLoaderData("draftName");

  useEffect(()=>{
    setIsLoaded(true)
  }, [loaderData])
  console.log(loaderData)

  return <App lines={loaderData} />;
  // return <>{!loaderData ? <LoadingAnimation /> : <App lines={loaderData} />}</>;
};

export default ReportDataHandler;

import { useLoaderData, useNavigation } from "react-router-dom";

import App from "./App";
import LoadingAnimation from "./components/LoadingAnimation";

const ReportDataHandler = () => {
  const loaderData = useLoaderData();
  const {state} = useNavigation();

  return state === "loading" ? <LoadingAnimation /> : <App lines={loaderData} />;
};

export default ReportDataHandler;

import { useLoaderData } from "react-router-dom";
import { ReportView } from "./ReportView";

const ReportDataHandler = () => {
  const loaderData = useLoaderData();

  return <ReportView lines={loaderData} />;
};

export default ReportDataHandler;

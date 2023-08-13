import { useLoaderData } from "react-router-dom";
import { ReportView } from "../../ReportView";

export const ImplementationDetails = () => {
    const loaderData = useLoaderData();
    return <ReportView reportData={loaderData} />
}

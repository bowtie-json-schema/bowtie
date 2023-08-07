import { useLoaderData } from "react-router-dom";
import { ReportView } from "../../ReportView";

export const PerImplementationPage = () => {
    const loaderData = useLoaderData();
    return <ReportView reportData={loaderData} />
}

PerImplementationPage;
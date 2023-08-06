import { useLoaderData } from "react-router-dom";

export const PerImplementationPage = () => {
    const implementationName = useLoaderData();

    return (
        <div>{implementationName}</div>
    )
}

PerImplementationPage;
import { describe, expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import NotFound from "./NotFound";

interface NotFoundTestParams {
    path: string,
    expectedText: string
}

const testCases: NotFoundTestParams[] = [
    {
        path: "/random-path",
        expectedText: "404 Not Found",
    }
]

describe.each(testCases)(
    "NotFound Component",
    ({ path, expectedText }) => {
        const testName = `Render correctly when navigating to '${path}'`;
        test(testName, () => {
        render(
            <MemoryRouter initialEntries={[path]}>
                <Routes>
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </MemoryRouter>
        );
        expect(screen.getByText(expectedText)).not.toBeNull();
    });
});


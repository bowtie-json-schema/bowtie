import { describe, expect, test } from "vitest";
import Dialect from "./Dialect";
import { complianceBadgeFor, versionsBadgeFor } from "./Badge";
import { Implementation } from "./parseReportData";

const mockImplementation: Implementation = {
  language: "javascript",
  name: "node",
  homepage: "",
  issues: "",
  source: "",
  dialects: [],
  results: {},
};

describe("Badge", () => {
  test("versionsBadgeFor should return the correct URL", () => {
    const expectedUrl = new URL(
      "https://img.shields.io/endpoint?url=https://bowtie.report/badges/javascript-node/supported_versions.json",
    );
    const badgeUrl = versionsBadgeFor(mockImplementation);
    expect(badgeUrl.href).toEqual(expectedUrl.href);
  });

  test("complianceBadgeFor should return the correct URL", () => {
    const expectedUrl = new URL(
      "https://img.shields.io/endpoint?url=https://bowtie.report/badges/javascript-node/compliance/draft7.json",
    );
    const badgeURL = complianceBadgeFor(
      mockImplementation,
      Dialect.withName("draft7"),
    );
    expect(badgeURL.href).toEqual(expectedUrl.href);
  });
});

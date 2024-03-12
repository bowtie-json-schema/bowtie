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
    const badgeUrl = versionsBadgeFor(mockImplementation);
    expect(badgeUrl.href()).toEqual(
      "https://img.shields.io/endpoint?url=http%3A%2F%2Flocalhost%3A3000%2Fbadges%2Fjavascript-node%2Fsupported_versions.json",
    );
  });

  test("complianceBadgeFor should return the correct URL", () => {
    const badgeURL = complianceBadgeFor(
      mockImplementation,
      Dialect.withName("draft7"),
    );
    expect(badgeURL.href()).toEqual(
      "https://img.shields.io/endpoint?url=http%3A%2F%2Flocalhost%3A3000%2Fbadges%2Fjavascript-node%2Fcompliance%2Fdraft7.json",
    );
  });
});

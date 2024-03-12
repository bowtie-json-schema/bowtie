import { describe, expect, test, vi, beforeEach } from "vitest";
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
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  test("versionsBadgeFor should return the correct URL", () => {
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost:8000",
      },
    });

    const badgeUrl = versionsBadgeFor(mockImplementation);
    expect(badgeUrl.href()).toEqual(
      "https://img.shields.io/endpoint?url=http%3A%2F%2Flocalhost%3A8000%2Fbadges%2Fjavascript-node%2Fsupported_versions.json"
    );
  });

  test("complianceBadgeFor should return the correct URL", () => {
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost:8000",
      },
    });

    const badgeURL = complianceBadgeFor(
      mockImplementation,
      Dialect.withName("draft7")
    );
    expect(badgeURL.href()).toEqual(
      "https://img.shields.io/endpoint?url=http%3A%2F%2Flocalhost%3A8000%2Fbadges%2Fjavascript-node%2Fcompliance%2Fdraft7.json"
    );
  });
});

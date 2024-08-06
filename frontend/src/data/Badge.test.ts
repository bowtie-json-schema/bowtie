import URI from "urijs";
import { describe, expect, test, vi } from "vitest";

// Mock the siteURI
vi.mock("./Site", () => ({
  default: new URI("https://example.com"),
}));
import { badgeFor, BADGES } from "./Badge";
import Implementation from "./Implementation";
import Dialect from "./Dialect";

const mockImplementation: Implementation =
  Implementation.withId("fake-javascript") ??
  new Implementation("fake-javascript", {
    name: "fake",
    language: "javascript",
    homepage: "",
    issues: "",
    source: "",
    dialects: [],
  });

describe("Badge", () => {
  test("BADGES URI", () => {
    expect(BADGES.href()).toEqual("https://example.com/badges");
  });

  test("badgeFor URI", () => {
    expect(badgeFor(BADGES).href()).toEqual(
      "https://img.shields.io/endpoint?url=https%3A%2F%2Fexample.com%2Fbadges",
    );
  });
});

describe("Implementation Badge", () => {
  test("versionsBadge function on the implementation should return the correct URL", () => {
    expect(mockImplementation.versionsBadge().href()).toEqual(
      "https://img.shields.io/endpoint?url=https%3A%2F%2Fexample.com%2Fbadges%2Fjavascript-fake%2Fsupported_versions.json",
    );
  });

  test("complianceBadgeFor function on the implementation should return the correct URL for the passed dialect", () => {
    expect(
      mockImplementation.complianceBadgeFor(Dialect.withName("draft7")).href(),
    ).toEqual(
      "https://img.shields.io/endpoint?url=https%3A%2F%2Fexample.com%2Fbadges%2Fjavascript-fake%2Fcompliance%2Fdraft7.json",
    );
  });
});

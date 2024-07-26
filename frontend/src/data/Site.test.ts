import { describe, expect, vi, test, beforeEach } from "vitest";

describe("siteURI", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  test("should be correct for development mode", async () => {
    vi.stubEnv("MODE", "development");
    vi.stubEnv("BASE_URL", "/");

    const { siteURI } = await import("./Site");

    expect(siteURI.href()).toEqual("https://bowtie.report/");
  });

  test("should be correct for other modes", async () => {
    vi.stubEnv("BASE_URL", "/");
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost:8000",
      },
    });

    const { siteURI } = await import("./Site");

    expect(siteURI.href()).toEqual("http://localhost:8000/");
  });
});

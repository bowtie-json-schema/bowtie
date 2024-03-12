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

describe("implementationMetadataURI", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  test("should be correct in development mode", async () => {
    vi.stubEnv("MODE", "development");
    vi.stubEnv("BASE_URL", "/");

    const { implementationMetadataURI } = await import("./Site");

    expect(implementationMetadataURI).toEqual(
      "https://bowtie.report/implementations.json"
    );
  });

  test("should be correct in other modes", async () => {
    vi.stubEnv("BASE_URL", "/");
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost:8000",
      },
    });

    const { implementationMetadataURI } = await import("./Site");

    expect(implementationMetadataURI).toEqual(
      "http://localhost:8000/implementations.json"
    );
  });
});

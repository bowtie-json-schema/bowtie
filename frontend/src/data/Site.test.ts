import { describe, expect, vi, test, afterEach } from "vitest";

describe("siteURI", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  test("should be correct for development mode", async () => {
    const originalEnv = { ...import.meta.env };
    vi.stubEnv("MODE", "development");
    vi.stubEnv("BASE_URL", "/");

    const { siteURI } = await import("./Site");

    expect(siteURI.href).toEqual("https://bowtie.report/");

    Object.assign(import.meta.env, originalEnv);
  });

  test("should be correct for production mode", async () => {
    const originalEnv = { ...import.meta.env };
    vi.stubEnv("MODE", "production");
    vi.stubEnv("BASE_URL", "/");

    const { siteURI } = await import("./Site");

    const productionURL = "http://localhost:3000/";
    vi.stubGlobal("window", {
      location: {
        href: new URL(productionURL),
      },
    });

    expect(siteURI.href).toEqual(`${productionURL}`);

    vi.unstubAllGlobals();
    Object.assign(import.meta.env, originalEnv);
  });
});

describe("implementationMetadataURI", () => {
  test("should be correct in development", async () => {
    const originalEnv = { ...import.meta.env };
    vi.stubEnv("MODE", "development");
    vi.stubEnv("BASE_URL", "/");

    const { implementationMetadataURI } = await import("./Site");

    expect(implementationMetadataURI).toEqual(
      "https://bowtie.report/implementations.json"
    );

    Object.assign(import.meta.env, originalEnv);
  });

  test("should be correct in production", async () => {
    const originalEnv = { ...import.meta.env };
    vi.stubEnv("MODE", "production");
    vi.stubEnv("BASE_URL", "/");

    const productionURL = "http://localhost:3000/";
    vi.stubGlobal("window", {
      location: {
        href: new URL(productionURL),
      },
    });

    const { implementationMetadataURI } = await import("./Site");

    expect(implementationMetadataURI).toEqual(
      "http://localhost:3000/implementations.json"
    );

    vi.unstubAllGlobals();
    Object.assign(import.meta.env, originalEnv);
  });
});

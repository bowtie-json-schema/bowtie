import { test, expect } from "@playwright/test";

import { serveRealWorldResults } from "./fixtures/realWorld";

const rows = ".rbars [data-impl]";

test.beforeEach(async ({ page }) => {
  await serveRealWorldResults(page);
});

test("ranks every implementation and links back to the benchmark", async ({ page }) => {
  await page.goto("/#/benchmarks");
  await page.waitForSelector(rows);

  // the fixture has 30 implementations
  await expect(page.locator(rows)).toHaveCount(30);
  await expect(
    page.getByRole("link", { name: "jsonschema-benchmark", exact: true }),
  ).toHaveAttribute("href", "https://github.com/sourcemeta-research/jsonschema-benchmark");
  await expect(page.getByRole("link", { name: "workflow run" })).toHaveAttribute(
    "href",
    /actions\/runs\/39017500063$/,
  );
});

test("links an implementation Bowtie tests to its Bowtie page", async ({ page }) => {
  await page.goto("/#/benchmarks");
  await page.waitForSelector(rows);

  await expect(page.locator(`${rows}[data-impl="boon"] a`)).toHaveAttribute(
    "href",
    "#/implementations/rust-boon",
  );
  // corvus-rs has no Bowtie ID in the fixture, so it is not a link
  await expect(page.locator(`${rows}[data-impl="corvus-rs"] a`)).toHaveCount(0);
  await expect(page.locator(`${rows}[data-impl="corvus-rs"] .cchip`)).toHaveText("not in Bowtie");
});

test("keeps only the implementations at 100% on the chosen dialect", async ({ page }) => {
  await page.goto("/#/benchmarks/draft7");
  await page.waitForSelector(rows);
  await expect(page.getByText(/pass\s+every Bowtie test of Draft 7/)).toBeVisible({ timeout: 30000 });

  const passing = await page.locator(`${rows} .cchip`, { hasText: /^100%$/ }).count();
  expect(passing).toBeGreaterThan(0);
  expect(passing).toBeLessThan(30);

  await page.getByRole("button", { name: "Only 100% on Draft 7" }).click();

  await expect(page.locator(rows)).toHaveCount(passing);
  for (const chip of await page.locator(`${rows} .cchip`).all()) {
    await expect(chip).toHaveText("100%");
  }
});

test("the dialect picker chooses which compliance counts", async ({ page }) => {
  await page.goto("/#/benchmarks/draft7");
  await page.waitForSelector(rows);

  await page.getByLabel("Choose dialect").selectOption("draft2020-12");

  await expect(page).toHaveURL(/#\/benchmarks\/draft2020-12$/);
  await expect(page.getByRole("button", { name: "Only 100% on Draft 2020-12" })).toBeVisible();
});

test("choosing a schema in the matrix shows its detail", async ({ page }) => {
  await page.goto("/#/benchmarks");
  await page.waitForSelector(rows);

  await page.locator(".rmatrix tbody th button", { hasText: "geojson" }).click();

  await expect(page.locator("#schema-detail select")).toHaveValue("geojson");
  await expect(page.locator(".sbars [data-impl]").first()).toBeVisible();
});

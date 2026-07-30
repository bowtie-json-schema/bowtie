import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Accessibility gate. Each key view is scanned with axe (WCAG 2.0/2.1 A + AA)
 * in both colour schemes; any violation fails the build. Pages render from the
 * live report data the dev server proxies, so we wait for real content first.
 */
interface Scenario {
  name: string;
  path: string;
  ready: string;
  /** optional interaction to reach a sub-view (e.g. open a case) before scanning */
  open?: (page: Page) => Promise<void>;
}

const scenarios: Scenario[] = [
  { name: "compliance report", path: "/#/", ready: ".shell .matrix .row" },
  {
    name: "case detail",
    path: "/#/",
    ready: ".shell .case-row",
    open: async (page) => {
      await page.locator(".case-row").first().click();
      await page.waitForSelector(".dis .ogroup", { timeout: 20000 });
    },
  },
  {
    name: "implementation",
    path: "/#/implementations/python-jsonschema",
    ready: "table.compliance tbody tr",
  },
  { name: "implementations index", path: "/#/implementations", ready: ".impl-card" },
  { name: "benchmarks", path: "/#/benchmarks", ready: ".bchart .brow" },
  { name: "upload", path: "/#/local-report", ready: ".dropzone" },
  { name: "not found", path: "/#/does-not-exist", ready: "h1" },
];

async function scan(page: Page) {
  const { violations } = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const summary = violations.map((v) => `${v.id} (${v.nodes.length})`).join(", ");
  expect(violations, summary).toEqual([]);
}

for (const scheme of ["light", "dark"] as const) {
  test.describe(`a11y (${scheme})`, () => {
    test.use({ colorScheme: scheme });
    for (const s of scenarios) {
      test(s.name, async ({ page }) => {
        await page.goto(s.path);
        await page.waitForSelector(s.ready, { timeout: 45000 });
        if (s.open) await s.open(page);
        await page.waitForTimeout(500);
        await scan(page);
      });
    }
  });
}

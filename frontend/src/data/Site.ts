const base =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;

export const siteURI = new URL(base);
siteURI.hash = "";
siteURI.pathname = new URL(import.meta.env.BASE_URL, base).pathname;

// FIXME: Presumably a future `Implementation` can handle the below, just
//        as `Dialect` handles it for dialect reports.
export const implementationMetadataURI = new URL(
  "implementations.json",
  siteURI,
).href;

export default siteURI;

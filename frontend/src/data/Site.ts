const base =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;

export const siteURI = new URL(base);
siteURI.hash = "";
siteURI.pathname = new URL(import.meta.env.BASE_URL, base).pathname;

export const implementationMetadataURI = new URL(
  "implementations.json",
  siteURI
).href;

export default siteURI;

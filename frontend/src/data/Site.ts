const base =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;

export const siteURL = new URL(base);
siteURL.hash = "";
siteURL.pathname = import.meta.env.BASE_URL;

export const implementationMetadataURL: string = new URL(
  "implementations.json",
  siteURL
).href;

export default siteURL;

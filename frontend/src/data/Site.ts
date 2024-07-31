import URI from "urijs";

const base =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;

export const siteURI = new URI(base)
  .fragment("")
  .directory(import.meta.env.BASE_URL);

export default siteURI;

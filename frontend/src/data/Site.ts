import URI from "urijs";

const base =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;

export const siteURI = new URI(base).directory(import.meta.env.BASE_URL);

// FIXME: Presumably a future `Implementation` can handle the below, just
//        as `Dialect` handles it for dialect reports.
export const implementationMetadataURI = siteURI
  .clone()
  .filename("implementations.json")
  .href();

export default siteURI;

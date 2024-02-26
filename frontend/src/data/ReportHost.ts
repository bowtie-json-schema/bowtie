import URI from "urijs";

export const reportHost =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;

export const reportUri = new URI(reportHost).directory(
  import.meta.env.BASE_URL
);

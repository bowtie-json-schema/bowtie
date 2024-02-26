import URI from "urijs";

const base =
  import.meta.env.MODE === "development"
    ? "https://bowtie.report"
    : window.location.href;

export default new URI(base).directory(import.meta.env.BASE_URL);

import type { Route } from "../stores/router.svelte";

export interface Section {
  name: Route["name"];
  label: string;
  href: string;
  /** route names for which this section is the active top-nav item */
  match: Route["name"][];
  /** parent section, for breadcrumb trails on drill-down pages */
  parent?: Route["name"];
  /** whether it appears in the primary top nav */
  inNav: boolean;
}

/**
 * Single source of truth for navigation: the top nav renders {@link NAV}, and
 * breadcrumbs walk `parent` links here. Renaming/re-parenting a section is a
 * one-line change — nothing is duplicated in page components.
 */
export const SECTIONS: Record<Route["name"], Section> = {
  dialect: {
    name: "dialect", label: "Compliance", href: "#/", match: ["dialect"], inNav: true,
  },
  benchmarks: {
    name: "benchmarks", label: "Benchmarks", href: "#/benchmarks", match: ["benchmarks"], inNav: true,
  },
  implementations: {
    name: "implementations", label: "Implementations", href: "#/implementations",
    match: ["implementations", "implementation"], inNav: true,
  },
  implementation: {
    name: "implementation", label: "Implementation", href: "#/implementations",
    match: [], parent: "implementations", inNav: false,
  },
  local: {
    name: "local", label: "Upload", href: "#/local-report", match: ["local"], inNav: true,
  },
  notfound: {
    name: "notfound", label: "Not found", href: "#/", match: [], inNav: false,
  },
};

export const NAV: Section[] = Object.values(SECTIONS).filter((s) => s.inNav);

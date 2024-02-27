import { Implementation } from "../data/parseReportData";
import Dialect from "./Dialect";
import { siteURL } from "./Site";

const SHIELDS = new URL("https://img.shields.io/endpoint");
const BADGES = new URL(siteURL);
BADGES.pathname += "/badges";

const badgeFor = (uri: URL): URL => {
  const shieldsURL = new URL(SHIELDS.href);
  shieldsURL.searchParams.append("url", uri.href);
  return shieldsURL;
};

const implementationBadges = (implementation: Implementation): URL => {
  const implementationId = `${implementation.language}-${implementation.name}`;
  const implementationURL = new URL(BADGES.href);
  implementationURL.pathname += `/${implementationId}`;
  return implementationURL;
};

export const versionsBadgeFor = (implementation: Implementation): URL =>
  badgeFor(
    new URL(
      implementationBadges(implementation).href + "/supported_versions.json"
    )
  );

export const complianceBadgeFor = (
  implementation: Implementation,
  dialect: Dialect
): URL => {
  const complianceURL = new URL(
    implementationBadges(implementation).href + "/compliance"
  );
  complianceURL.pathname += `/${dialect.path}.json`;
  return badgeFor(complianceURL);
};

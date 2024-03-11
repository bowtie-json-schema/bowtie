import { Implementation } from "../data/parseReportData";
import Dialect from "./Dialect";
import siteURI from "./Site";

const SHIELDS = new URL("https://img.shields.io/endpoint");

const BADGES = new URL(siteURI.toString());
BADGES.pathname += "/badges";

const badgeFor = (url: URL): URL =>
  new URL(SHIELDS.toString() + "?url=" + encodeURIComponent(url.toString()));

const implementationBadges = (implementation: Implementation): URL => {
  const implementationId = `${implementation.language}-${implementation.name}`;
  const url = new URL(BADGES.toString());
  url.pathname += "/" + implementationId;
  return url;
};

export const versionsBadgeFor = (implementation: Implementation): URL =>
  badgeFor(
    new URL(
      implementationBadges(implementation).toString() +
        "/supported_versions.json"
    )
  );

export const complianceBadgeFor = (
  implementation: Implementation,
  dialect: Dialect
): URL =>
  badgeFor(
    new URL(
      implementationBadges(implementation).toString() +
        "/compliance/" +
        dialect.shortName +
        ".json"
    )
  );

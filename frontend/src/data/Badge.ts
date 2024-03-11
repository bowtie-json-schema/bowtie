import { Implementation } from "../data/parseReportData";
import Dialect from "./Dialect";
import siteURI from "./Site";

const SHIELDS = new URL("https://img.shields.io/endpoint");

const BADGES = new URL(`${siteURI.href}/badges`);

const badgeFor = (url: URL): URL => {
  const shieldsURL = new URL(SHIELDS);
  shieldsURL.searchParams.set("url", url.href);
  return shieldsURL;
};

const implementationBadges = (implementation: Implementation): URL => {
  const implementationId = `${implementation.language}-${implementation.name}`;
  return new URL(`${BADGES.href}/${implementationId}`);
};

export const versionsBadgeFor = (implementation: Implementation): URL =>
  badgeFor(
    new URL(
      `${implementationBadges(implementation).href}/supported_versions.json`,
    ),
  );

export const complianceBadgeFor = (
  implementation: Implementation,
  dialect: Dialect,
): URL =>
  badgeFor(
    new URL(
      `${implementationBadges(implementation).href}/compliance/${
        dialect.shortName
      }.json`,
    ),
  );

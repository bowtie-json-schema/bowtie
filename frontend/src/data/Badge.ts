import URI from "urijs";

import { Implementation } from "../data/parseReportData";
import Dialect from "./Dialect";
import siteURI from "./Site";

const SHIELDS = new URI("https://img.shields.io/endpoint");

const BADGES = siteURI.clone().segment("badges");

const badgeFor = (uri: URI): URI => SHIELDS.clone().addQuery("url", uri);

// FIXME: probably all the below belongs in Implementation
const implementationBadges = (implementation: Implementation): URI => {
  const implementationId = `${implementation.language}-${implementation.name}`;
  return BADGES.clone().segment(implementationId);
};

export const versionsBadgeFor = (implementation: Implementation): URI =>
  badgeFor(
    implementationBadges(implementation)
      .clone()
      .segment("supported_versions.json"),
  );

export const complianceBadgeFor = (
  implementation: Implementation,
  dialect: Dialect,
): URI =>
  badgeFor(
    implementationBadges(implementation)
      .clone()
      .segment("compliance")
      .segment(dialect.shortName)
      .suffix("json"),
  );

export interface Badge {
  name: string;
  uri: URI;
  altText: string;
}

export function badgesFor(implementation: Implementation) {
  return {
    // FIXME: Include the result in alt text, not just the label
    Metadata: [
      {
        name: "Supported Dialects",
        altText: "Supported Dialects",
        uri: versionsBadgeFor(implementation),
      },
    ],
    "Specification Compliance": implementation.dialects.map((uri) => {
      const dialect = Dialect.forURI(uri); // FIXME
      return {
        name: dialect.prettyName,
        altText: dialect.prettyName,
        uri: complianceBadgeFor(implementation, dialect),
      };
    }),
  };
}

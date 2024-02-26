import URI from "urijs";
import siteURI from "./Site";

import { Implementation } from "../data/parseReportData";
import Dialect from "../data/Dialect";

const BADGES = siteURI.clone().directory("badges");

const SHIELDS = new URI("https://img.shields.io/endpoint");

const badgeFor = (uri: URI): URI => SHIELDS.addSearch("url", uri);

export const complianceBadgeFor = (
  implementation: Implementation,
  dialect: Dialect,
): URI => {
  // FIXME: obviously this belongs in Implementation
  const implementationId = `${implementation.language}-${implementation.name}`;
  const implementationBadges = BADGES.clone().directory(implementationId);
  return badgeFor(
    implementationBadges
      .directory("compliance")
      .filename(`${dialect.path}.json`),
  );
};

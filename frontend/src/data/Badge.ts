import URI from "urijs";

import siteURI from "./Site";

const SHIELDS = new URI("https://img.shields.io/endpoint");

export const BADGES = siteURI.clone().segment("badges");

export const badgeFor = (uri: URI): URI => SHIELDS.clone().addQuery("url", uri);

export interface Badge {
  name: string;
  uri: URI;
  altText: string;
}

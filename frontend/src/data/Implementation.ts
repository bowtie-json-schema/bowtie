import URI from "urijs";

import { badgeFor, BADGES } from "./Badge";
import Dialect from "./Dialect";
import siteURI from "./Site";

export interface RawImplementationData {
  language: string;
  name: string;
  version?: string;
  dialects: string[];
  homepage: string;
  documentation?: string;
  issues: string;
  source: string;
  links?: {
    description?: string;
    url?: string;
    [k: string]: unknown;
  }[];
  os?: string;
  os_version?: string;
  language_version?: string;
}

/**
 * An individual implementation of JSON Schema supported by Bowtie.
 */
export default class Implementation
  implements Omit<RawImplementationData, "dialects">
{
  readonly language!: string;
  readonly name!: string;
  readonly version?: string;
  readonly dialects!: Dialect[];
  readonly homepage!: string;
  readonly documentation?: string;
  readonly issues!: string;
  readonly source!: string;
  readonly links?: {
    description?: string;
    url?: string;
    [k: string]: unknown;
  }[];
  readonly os?: string;
  readonly os_version?: string;
  readonly language_version?: string;
  readonly routePath!: string;

  private static all: Map<string, Implementation> = new Map<
    string,
    Implementation
  >();

  constructor(id: string, rawData: RawImplementationData) {
    if (Implementation.all.has(id)) {
      return Implementation.all.get(id)!;
    } else {
      Implementation.all.set(id, this);
    }

    this.language = rawData.language;
    this.name = rawData.name;
    this.version = rawData.version;
    this.dialects = rawData.dialects.map((uri) => Dialect.forURI(uri));
    this.homepage = rawData.homepage;
    this.documentation = rawData.documentation;
    this.issues = rawData.issues;
    this.source = rawData.source;
    this.links = rawData.links;
    this.os = rawData.os;
    this.os_version = rawData.os_version;
    this.language_version = rawData.language_version;
    this.routePath = `/implementations/${id}`;
  }

  static async fetchAllImplementationsData() {
    const url = siteURI
      .clone()
      .segment("implementations")
      .suffix("json")
      .href();
    const response = await fetch(url);
    const rawImplementations = (await response.json()) as Record<
      string,
      RawImplementationData
    >;

    Object.entries(rawImplementations).forEach(
      ([id, rawData]) => new Implementation(id, rawData),
    );

    return this.all;
  }

  private get badgesIdSegment(): URI {
    return BADGES.clone().segment(`${this.language}-${this.name}`);
  }

  versionsBadge(): URI {
    return badgeFor(
      this.badgesIdSegment.clone().segment("supported_versions").suffix("json"),
    );
  }

  complianceBadgeFor(dialect: Dialect): URI {
    return badgeFor(
      this.badgesIdSegment
        .clone()
        .segment("compliance")
        .segment(dialect.shortName)
        .suffix("json"),
    );
  }

  badges() {
    return {
      // FIXME: Include the result in alt text, not just the label
      Metadata: [
        {
          name: "Supported Dialects",
          altText: "Supported Dialects",
          uri: this.versionsBadge(),
        },
      ],
      "Specification Compliance": this.dialects.map((dialect) => {
        return {
          name: dialect.prettyName,
          altText: dialect.prettyName,
          uri: this.complianceBadgeFor(dialect),
        };
      }),
    };
  }
}

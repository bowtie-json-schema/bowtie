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
  private readonly id: string;
  readonly language: string;
  readonly name: string;
  readonly version?: string;
  readonly dialects: Dialect[];
  readonly homepage: string;
  readonly documentation?: string;
  readonly issues: string;
  readonly source: string;
  readonly links?: {
    description?: string;
    url?: string;
    [k: string]: unknown;
  }[];
  readonly os?: string;
  readonly os_version?: string;
  readonly language_version?: string;
  readonly routePath: string;

  constructor(
    implementationId: string,
    rawImplementationData: RawImplementationData,
  ) {
    this.id = implementationId;
    this.language = rawImplementationData.language;
    this.name = rawImplementationData.name;
    this.version = rawImplementationData.version;
    this.dialects = rawImplementationData.dialects.map((uri) =>
      Dialect.forURI(uri),
    );
    this.homepage = rawImplementationData.homepage;
    this.documentation = rawImplementationData.documentation;
    this.issues = rawImplementationData.issues;
    this.source = rawImplementationData.source;
    this.links = rawImplementationData.links;
    this.os = rawImplementationData.os;
    this.os_version = rawImplementationData.os_version;
    this.language_version = rawImplementationData.language_version;
    this.routePath = `/implementations/${implementationId}`;
  }

  static async fetchAllImplementationsMetadata() {
    const url = siteURI
      .clone()
      .segment("implementations")
      .suffix("json")
      .href();
    const response = await fetch(url);
    return (await response.json()) as Record<string, RawImplementationData>;
  }

  private idSegment(): URI {
    return BADGES.clone().segment(this.id);
  }

  versionsBadge(): URI {
    return badgeFor(
      this.idSegment().clone().segment("supported_versions").suffix("json"),
    );
  }

  complianceBadgeFor(dialect: Dialect): URI {
    return badgeFor(
      this.idSegment()
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

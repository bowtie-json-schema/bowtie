import URI from "urijs";

import { badgeFor, BADGES } from "./Badge";
import Dialect from "./Dialect";
import siteURI from "./Site";
import { fromSerialized, ReportData } from "./parseReportData";

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
  readonly id: string;
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
  private _versions?: string[];

  private static all: Map<string, Implementation> = new Map<
    string,
    Implementation
  >();

  constructor(id: string, rawData: RawImplementationData) {
    Implementation.all.set(id, this);

    this.id = id;
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

  static withId(id: string) {
    return this.all.get(id);
  }

  static async fetchAllImplementationsData(baseURI: URI = siteURI) {
    const url = baseURI
      .clone()
      .segment("implementations")
      .suffix("json")
      .href();
    const response = await fetch(url);
    const rawImplementations = (await response.json()) as Record<
      string,
      RawImplementationData
    >;
    const parsedImplementations = new Map<string, Implementation>();

    Object.entries(rawImplementations).forEach(([id, rawData]) =>
      parsedImplementations.set(
        id,
        this.withId(id) ?? new Implementation(id, rawData),
      ),
    );

    return parsedImplementations;
  }

  private directoryURI(baseURI: URI = siteURI) {
    return baseURI.clone().directory("implementations").filename(this.id);
  }

  get versions() {
    return this._versions ? [...this._versions] : undefined;
  }

  async fetchVersions(baseURI: URI = siteURI) {
    const versionsURI = this.directoryURI(baseURI)
      .clone()
      .segment("matrix-versions")
      .suffix("json")
      .href();

    try {
      const response = await fetch(versionsURI);
      this._versions = (await response.json()) as string[];
      return this.versions;
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      this._versions = undefined;
      return this.versions;
    }
  }

  async fetchVersionedReportsFor(dialect: Dialect, baseURI: URI = siteURI) {
    const versions = this.versions;
    if (!versions)
      throw new ImplementationError(
        `No versions metadata found for ${this.id} implementation.`,
      );

    const versionedReportsData = new Map<string, ReportData>();
    await Promise.all(
      versions.map(async (version) => {
        try {
          const response = await fetch(
            this.directoryURI(baseURI)
              .clone()
              .segment(`v${version}`)
              .segment(dialect.shortName)
              .suffix("json")
              .href(),
          );
          versionedReportsData.set(
            version,
            fromSerialized(await response.text()),
          );
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (error) {
          return;
        }
      }),
    );

    return versionedReportsData;
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

class ImplementationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ImplementationError";
    Object.setPrototypeOf(this, ImplementationError.prototype);
  }
}

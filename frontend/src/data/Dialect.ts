import data from "../../../data/dialects.json";
import { fromSerialized } from "./parseReportData";
import { siteURL } from "./Site";

export default class Dialect {
  readonly shortName: string;
  readonly prettyName: string;
  readonly uri: string;
  readonly firstPublicationDate: Date;

  private static all: Map<string, Dialect> = new Map<string, Dialect>();

  constructor(
    shortName: string,
    prettyName: string,
    uri: string,
    firstPublicationDate: Date,
  ) {
    if (Dialect.all.has(shortName)) {
      throw new DialectError(`A "${shortName}" dialect already exists.`);
    }
    Dialect.all.set(shortName, this);

    this.shortName = shortName;
    this.prettyName = prettyName;
    this.uri = uri;
    this.firstPublicationDate = firstPublicationDate;
  }

  async fetchReport(baseURI: URI = siteURI) {
    const url = baseURI.clone().filename(this.shortName).suffix("json").href();
    const response = await fetch(url);
    return fromSerialized(await response.text());
  }

  static known(): Iterable<Dialect> {
    return Dialect.all.values();
  }

  static newest_to_oldest(): Dialect[] {
    return Array.from(Dialect.known()).sort(
      (d1: Dialect, d2: Dialect) =>
        d2.firstPublicationDate.valueOf() - d1.firstPublicationDate.valueOf(),
    );
  }

  static withName(shortName: string): Dialect {
    const dialect = Dialect.all.get(shortName);
    if (!dialect) {
      throw new DialectError(`A ${shortName} dialect does not exist.`);
    }
    return dialect;
  }

  static forURI(uri: string): Dialect {
    const dialect = Array.from(Dialect.all.entries()).find(
      ([, dialect]) => dialect.uri === uri,
    );
    if (!dialect) {
      throw new DialectError(`A ${uri} dialect does not exist.`);
    }
    return dialect[1];
  }
}

class DialectError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DialectError";
    Object.setPrototypeOf(this, DialectError.prototype);
  }
}

for (const each of data) {
  new Dialect(
    each.shortName,
    each.prettyName,
    each.uri,
    new Date(each.firstPublicationDate),
  );
}

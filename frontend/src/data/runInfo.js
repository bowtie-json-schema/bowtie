import Summary from "./summary";

const _DIALECT_URI_TO_SHORTNAME = {
  "https://json-schema.org/draft/2020-12/schema": "Draft 2020-12",
  "https://json-schema.org/draft/2019-09/schema": "Draft 2019-09",
  "http://json-schema.org/draft-07/schema#": "Draft 7",
  "http://json-schema.org/draft-06/schema#": "Draft 6",
  "http://json-schema.org/draft-04/schema#": "Draft 4",
  "http://json-schema.org/draft-03/schema#": "Draft 3",
};

export class RunInfo {
  constructor(lines) {
    this.lines = lines;
    const runInfoData = this.lines[0];
    this.started = runInfoData.started;
    this.bowtieVersion = runInfoData.bowtie_version;
    this.dialect = runInfoData.dialect;
    this.implementations = runInfoData.implementations;
    this.metadata = runInfoData.metadata;
  }

  get dialect_shortname() {
    return _DIALECT_URI_TO_SHORTNAME[this.dialect] || this.dialect;
  }

  static from_implementations(implementations, dialect) {
    const now = new Date();
    return new RunInfo(
      now.toISOString(),
      importlib.metadata.version("bowtie-json-schema"),
      dialect,
      Object.fromEntries(
        implementations.map((implementation) => [
          implementation.name,
          {
            ...implementation.metadata,
            image: implementation.name,
          },
        ]),
      ),
    );
  }

  createSummary() {
    return new Summary(this.lines);
  }
}

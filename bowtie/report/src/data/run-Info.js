export class RunInfo {
  constructor(runInfoData) {
    // console.log(runInfoData.metadata)
    this.started = runInfoData.started;
    this.bowtie_version = runInfoData.bowtie_version;
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
        ])
      )
    );
  }

  create_summary() {
    console.log(Object.values(this._implementations));
    return new _Summary({
      implementations: Object.values(this._implementations),
    });
  }
}

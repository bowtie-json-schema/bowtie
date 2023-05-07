const attrs = require('attrs');
const importlib = require('importlib');

const _DIALECT_URI_TO_SHORTNAME = {
  "https://json-schema.org/draft/2020-12/schema": "Draft 2020-12",
  "https://json-schema.org/draft/2019-09/schema": "Draft 2019-09",
  "http://json-schema.org/draft-07/schema#": "Draft 7",
  "http://json-schema.org/draft-06/schema#": "Draft 6",
  "http://json-schema.org/draft-04/schema#": "Draft 4",
  "http://json-schema.org/draft-03/schema#": "Draft 3",
};

class RunInfo {
  constructor(started, bowtie_version, dialect, _implementations) {
    this.started = started;
    this.bowtie_version = bowtie_version;
    this.dialect = dialect;
    this._implementations = _implementations;
  }

  get dialect_shortname() {
    return _DIALECT_URI_TO_SHORTNAME.get(this.dialect, this.dialect);
  }

  static from_implementations(implementations, dialect) {
    const now = new Date();
    return new RunInfo(
      now.toISOString(),
      importlib.metadata.version("bowtie-json-schema"),
      dialect,
      Object.fromEntries(implementations.map((implementation) => [
        implementation.name,
        {
          ...implementation.metadata,
          image: implementation.name,
        }
      ]))
    );
  }

  create_summary() {
    return new _Summary({ implementations: Object.values(this._implementations) });
  }
}

RunInfo._implementations = attrs.field({ alias: 'implementations' });

class _Summary {
  constructor(implementations) {
    this.implementations = implementations;
  }
}

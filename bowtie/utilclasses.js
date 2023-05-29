// import attrs from 'https://cdn.jsdelivr.net/npm/attrs@2.2.0/dist/attrs.min.js';

// import * as importlib from 'https://unpkg.com/importlib';

class InvalidBowtieReport extends Error {
  constructor(message) {
    super(message);
    this.name = "InvalidBowtieReport";
  }
}

const _DIALECT_URI_TO_SHORTNAME = {
  "https://json-schema.org/draft/2020-12/schema": "Draft 2020-12",
  "https://json-schema.org/draft/2019-09/schema": "Draft 2019-09",
  "http://json-schema.org/draft-07/schema#": "Draft 7",
  "http://json-schema.org/draft-06/schema#": "Draft 6",
  "http://json-schema.org/draft-04/schema#": "Draft 4",
  "http://json-schema.org/draft-03/schema#": "Draft 3",
};

export class RunInfo {
  constructor(started, bowtie_version, dialect, _implementations) {
    this.started = started;
    this.bowtie_version = bowtie_version;
    this.dialect = dialect;
    this._implementations = _implementations;
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

  create_summary() {
    // console.log(Object.values(this._implementations))
    // console.log((this._implementations))
    return new _Summary({
      implementations: Object.values(this._implementations),
    });
  }
}

RunInfo._implementations = {
  alias: "implementations",
  validate: (value) => {
    if (!Array.isArray(value)) {
      throw new Error('The "implementations" attribute must be an array.');
    }
    return true;
  },
};

//////////////////////////////////
// Summary class

class _Summary {
  constructor(implementations) {
    // console.log(typeof(implementations.implementations))
    // console.log((implementations['implementations']))
    const implementationArray = Object.values(implementations);
    // console.log(implementationArray[0])

    this.implementations = implementationArray[0].sort((each, other) => {
      const key = `${each.language}${each.name}`;
      const otherKey = `${other.language}${other.name}`;
      return key < otherKey ? -1 : 1;
    });
    // console.log(this.implementations)

    this._combined = {};
    // console.log(this._combined)
    this.did_fail_fast = false;
    this.counts = {};

    this.initializeCounts();
    // console.log(this.counts)
  }

  initializeCounts() {
    for (const each of this.implementations) {
      this.counts[each.image] = new Count();
    }
  }

  get total_cases() {
    const counts = new Set(
      Object.values(this.counts).map((count) => count.total_cases),
    );
    // console.log(counts)
    if (counts.size !== 1) {
      const summary = Object.entries(this.counts)
        .map(
          ([each, count]) => `  ${each.split("/").pop()}: ${count.total_cases}`,
        )
        .join("\n");
      throw new InvalidBowtieReport(
        `Inconsistent number of cases run:\n\n${summary}`,
      );
    }
    return counts.values().next().value;
  }

  get errored_cases() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.errored_cases,
      0,
    );
  }

  get total_tests() {
    const counts = new Set(
      Object.values(this.counts).map((count) => count.total_tests),
    );
    // console.log(counts)
    // if (counts.size !== 1) {
    //   throw new InvalidBowtieReport(`Inconsistent number of tests run: ${JSON.stringify(this.counts)}`);
    // }
    return counts.values().next().value;
  }

  get failed_tests() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.failed_tests,
      0,
    );
  }

  get errored_tests() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.errored_tests,
      0,
    );
  }

  get skipped_tests() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.skipped_tests,
      0,
    );
  }

  // add_case_metadata(seq, caseMetadata)
  add_case_metadata(caseObject) {
    const results = caseObject.case.tests.map((test) => [test, {}]);
    this._combined[caseObject.seq] = {
      case: caseObject.case,
      results: results,
    };
  }

  // see_error(implementation, seq, context, caught)
  see_error(implementationObject) {
    const count = this.counts[implementationObject.implementation];
    count.total_cases += 1;
    count.errored_cases += 1;

    const caseMetadata = this._combined[implementationObject.seq].case;
    count.total_tests += caseMetadata.tests.length;
    count.errored_tests += caseMetadata.tests.length;
  }

  see_result(result) {
    const count = this.counts[result.implementation];
    count.total_cases += 1;

    const combined = this._combined[result.seq].results;

    for (let i = 0; i < result.compare().length; i++) {
      const [test, failed] = result.compare()[i];
      const [, seen] = combined[i];
      count.total_tests += 1;
      if (test.skipped) {
        count.skipped_tests += 1;
        seen[result.implementation] = [test.reason, "skipped"];
      } else if (test.errored) {
        count.errored_tests += 1;
        seen[result.implementation] = [test.reason, "errored"];
      } else {
        if (failed) {
          count.failed_tests += 1;
        }
        seen[result.implementation] = [test, failed];
      }
    }
  }

  see_skip(skipped) {
    const count = this.counts[skipped.implementation];
    count.total_cases += 1;

    const case_data = this._combined[skipped.seq].case;
    count.total_tests += case_data.tests.length;
    count.skipped_tests += case_data.tests.length;

    for (const [, seen] of this._combined[skipped.seq].results) {
      const message = skipped.issue_url || skipped.message || "skipped";
      seen[skipped.implementation] = [message, "skipped"];
    }
  }

  see_maybe_fail_fast(did_fail_fast) {
    this.did_fail_fast = did_fail_fast;
  }

  case_results() {
    return Object.values(this._combined).map((each) => ({
      case: each.case,
      registry: each.registry || {},
      results: each.results,
    }));
  }

  *flat_results() {
    let sorted_CombinedArray = Object.entries(this._combined).sort(
      ([keyA, valueA], [keyB, valueB]) => {
        if (keyA < keyB) {
          return -1;
        } else if (keyA > keyB) {
          return 1;
        } else {
          return 0;
        }
      },
    );
    let sorted_CombinedObject = Object.fromEntries(sorted_CombinedArray);
    // console.log(sorted_CombinedObject)
    for (let seq in sorted_CombinedObject) {
      let each = sorted_CombinedObject[seq];
      const caseData = each["case"];
      yield [
        seq,
        caseData["description"],
        caseData["schema"],
        caseData["registry"],
        each["results"],
      ];
    }
  }

  generate_badges(target_dir, dialect) {
    const label = _DIALECT_URI_TO_SHORTNAME[dialect];
    for (const impl of this.implementations) {
      if (!impl.dialects.includes(dialect)) continue;

      const name = impl.name;
      const lang = impl.language;
      const counts = this.counts[impl.image];
      const total = counts.total_tests;
      const passed =
        total -
        counts.failed_tests -
        counts.errored_tests -
        counts.skipped_tests;
      const pct = (passed / total) * 100;
      const impl_dir = target_dir.join(`${lang}-${name}`);
      fs.mkdirSync(impl_dir, { recursive: true });

      const [r, g, b] = [100 - Math.floor(pct), Math.floor(pct), 0];
      const badge = {
        schemaVersion: 1,
        label: label,
        message: `${Math.floor(pct)}% Passing`,
        color: `${r.toString(16).padStart(2, "0")}${g
          .toString(16)
          .padStart(2, "0")}${b.toString(16).padStart(2, "0")}`,
      };
      const badge_path = impl_dir.join(`${label.replace(" ", "_")}.json`);
      fs.writeFileSync(badge_path, JSON.stringify(badge));
    }
  }
}

// class Counts

class Count {
  constructor() {
    this.total_cases = 0;
    this.errored_cases = 0;
    this.total_tests = 0;
    this.failed_tests = 0;
    this.errored_tests = 0;
    this.skipped_tests = 0;
  }

  unsuccessful_tests() {
    return this.errored_tests + this.failed_tests + this.skipped_tests;
  }
}

// Unused classes till now
// class ClaseSkipped

export class CaseSkipped {
  // constructor(implementation, seq, message = null, issue_url = null)
  constructor(object, message = null, issue_url = null) {
    this.errored = false;
    this.implementation = object.implementation;
    this.seq = object.seq;
    this.message = message;
    this.issue_url = issue_url;
    this.skipped = true;
  }

  report(reporter) {
    reporter.skipped(this);
  }
}

// class CaseResult
export class CaseResult {
  errored = false;
  implementation;
  seq;
  results;
  expected;
  static from_dict(data, kwargs) {
    return new CaseResult({
      results: data.results.map((t) => TestResult.from_dict(t)),
      ...data,
      ...kwargs,
    });
  }

  get failed() {
    return Array.from(this.compare()).some(([, failed]) => failed);
  }

  report(reporter) {
    reporter.got_results(this);
  }

  *compare() {
    for (let i = 0; i < this.results.length; i++) {
      const test = this.results[i];
      const expected = this.expected[i];
      const failed =
        !test.skipped &&
        !test.errored &&
        expected !== null &&
        expected !== test.valid;
      yield [test, failed];
    }
  }

  constructor({ implementation, seq, results, expected }) {
    this.errored = false;

    this.implementation = implementation;

    this.seq = seq;

    this.results = results;

    this.expected = expected;
  }
}

//class TestResult

class TestResult {
  static errored = false;
  static skipped = false;
  valid;

  constructor(valid) {
    this.valid = valid;
  }

  static from_dict(data) {
    if (data.skipped) {
      return new SkippedTest(data);
    } else if (data.errored) {
      return new ErroredTest(data);
    }
    return new TestResult(data.valid);
  }
}

//class SkippedTest

class SkippedTest {
  constructor(message = null, issue_url = null) {
    this.message = message;
    this.issue_url = issue_url;
    this.errored = false;
    this.skipped = true;
  }

  get reason() {
    if (this.message !== null) {
      return this.message;
    }
    if (this.issue_url !== null) {
      return this.issue_url;
    }
    return "skipped";
  }
}

//class ErroredTest

class ErroredTest {
  constructor(context = {}) {
    this.context = context;
    this.errored = true;
    this.skipped = false;
  }

  get reason() {
    const message = this.context["message"];
    if (message) {
      return message;
    }
    return "Encountered an error.";
  }
}

//class ReportData

class ReportData {
  constructor(summary, run_info, generate_dialect_navigation) {
    this.summary = summary;
    this.run_info = run_info;
    this.generate_dialect_navigation = generate_dialect_navigation;
  }
}

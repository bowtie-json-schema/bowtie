export function schemaDisplay(parentBodyId, code, targetId, rowClass) {
  let currentParentBodyId = null;
  const displayBody = document.getElementById("display-body");

  if (parentBodyId !== currentParentBodyId) {
    currentParentBodyId = parentBodyId;
    displayBody.classList.remove("d-none");
    displayBody.classList.add("d-block");
    document.getElementById("instance-info").innerHTML = "";

    const isDisplayed =
      displayBody.parentElement === document.getElementById(parentBodyId);

    if (isDisplayed) {
      displayBody.parentElement.removeChild(displayBody);
    } else {
      // Add Highlight Row Functionality to clicked accordion only
      rowHighlightListener(rowClass);
      displayCode(code, targetId);
      const accordionBody = document.querySelector(`#${parentBodyId}`);
      accordionBody.insertBefore(displayBody, accordionBody.firstChild);
    }
  }
}

function rowHighlightListener(rowClass) {
  const instanceRows = document.getElementsByClassName(rowClass);
  for (let i = 0; i < instanceRows.length; i++) {
    const currentInstanceRow = instanceRows[i];
    currentInstanceRow.addEventListener("click", function () {
      const activeElements = document.getElementsByClassName("table-active");
      for (let j = 0; j < activeElements.length; j++) {
        activeElements[j].classList.remove("table-active");
      }
      currentInstanceRow.classList.add("table-active");
    });
  }
}

function displayCode(code, targetId) {
  const targetDisplay = document.getElementById(targetId);
  displayBody.classList.remove("d-none");
  displayBody.classList.add("d-block");
  targetDisplay.innerHTML = `<pre>${code}</pre>`;
}

export function to_icon(valid) {
  if (valid === true) {
    // Circular Checkmark SVG Icon
    return `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check-circle-fill" viewBox="0 0 16 16">
          <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z" />
        </svg>
      `;
  } else if (valid === false) {
    // Circular cross (x) SVG Icon
    return `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-circle-fill" viewBox="0 0 16 16">
          <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z" />
        </svg>
      `;
  } else {
    // Circular warning (!) SVG Icon
    return `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-octagon" viewBox="0 0 16 16">
          <path d="M4.54.146A.5.5 0 0 1 4.893 0h6.214a.5.5 0 0 1 .353.146l4.394 4.394a.5.5 0 0 1 .146.353v6.214a.5.5 0 0 1-.146.353l-4.394 4.394a.5.5 0 0 1-.353.146H4.893a.5.5 0 0 1-.353-.146L.146 11.46A.5.5 0 0 1 0 11.107V4.893a.5.5 0 0 1 .146-.353L4.54.146zM5.1 1 1 5.1v5.8L5.1 15h5.8l4.1-4.1V5.1L10.9 1H5.1z" />
          <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z" />
        </svg>
      `;
  }
}






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
      Object.values(this.counts).map((count) => count.total_cases)
    );
    // console.log(counts)
    if (counts.size !== 1) {
      const summary = Object.entries(this.counts)
        .map(
          ([each, count]) => `  ${each.split("/").pop()}: ${count.total_cases}`
        )
        .join("\n");
      throw new InvalidBowtieReport(
        `Inconsistent number of cases run:\n\n${summary}`
      );
    }
    return counts.values().next().value;
  }

  get errored_cases() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.errored_cases,
      0
    );
  }

  get total_tests() {
    const counts = new Set(
      Object.values(this.counts).map((count) => count.total_tests)
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
      0
    );
  }

  get errored_tests() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.errored_tests,
      0
    );
  }

  get skipped_tests() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.skipped_tests,
      0
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
      }
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

// class _CaseReport

class _CaseReporter {
  constructor(write, log) {
    this.write = write;
    this.log = log;
  }

  static case_started(log, write, caseObj, seq) {
    const self = new _CaseReporter(write, log);
    self.write({ case: caseObj, seq });
    return self;
  }

  got_results(results) {
    this.write(results);
  }

  skipped(skipped) {
    this.write(skipped);
  }

  no_response(implementation) {
    this.log.error("No response", { logger_name: implementation });
  }

  errored(results) {
    const { implementation, context } = results;
    const message = results.caught ? "" : "uncaught error";
    this.log.error(message, { logger_name: implementation, ...context });
    this.got_results(results);
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

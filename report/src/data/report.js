class Summary {
  constructor(lines) {
    this.lines = lines;
    const runInfoData = this.lines[0];
    const implementationsArray = Object.values(runInfoData.implementations);

    this.implementations = implementationsArray.sort((each, other) => {
      const key = `${each.language}${each.name}`;
      const otherKey = `${other.language}${other.name}`;
      return key < otherKey ? -1 : 1;
    });
    this.didFailFast = false;
  }
}

export class Count {
  constructor() {
    this.total_cases = 0;
    this.errored_cases = 0;
    this.total_tests = 0;
    this.failed_tests = 0;
    this.errored_tests = 0;
    this.skipped_tests = 0;
  }

  addTotalErroredCases(value) {
    this.errored_cases += value;
  }

  addTotalFailedTests(value) {
    this.failed_tests += value;
  }

  addTotalErroredTests(value) {
    this.errored_tests += value;
  }
  addTotalSkippedTests(value) {
    this.skipped_tests += value;
  }

  unsuccessful_tests() {
    return this.errored_tests + this.failed_tests + this.skipped_tests;
  }
}

export default Summary;

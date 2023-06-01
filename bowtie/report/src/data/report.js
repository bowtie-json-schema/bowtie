class Summary {
  constructor(lines) {
    // console.log((implementations))

    this.lines = lines;
    const runInfoData = this.lines[0];
    const implementationsArray = Object.values(runInfoData.implementations);
    // console.log(implementationsArray)

    this.implementations = implementationsArray.sort((each, other) => {
      const key = `${each.language}${each.name}`;
      const otherKey = `${other.language}${other.name}`;
      return key < otherKey ? -1 : 1;
    });
    this.did_fail_fast = false;
    this.counts = {};
    // console.log(this.counts)
    this.initializeCounts();
  }
  initializeCounts(){
    for (const each of this.implementations) {
      this.counts[each.image] = new Count();
    }
  }

    get total_cases() {
      var count  = 0;
      this.lines.forEach(element => {
        const firstKey = Object.keys(element)[0];
        if (firstKey == 'case'){
          count+=1;
        }
      });
      return count;
  }

  get total_tests() {
    var count = 0;
    this.lines.forEach(element => {
      const firstKey = Object.keys(element)[0];
      if (firstKey == 'case'){
        count += element['case']['tests'].length;
      }
    });
    return count;
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

  get errored_cases() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.errored_cases,
      0,
    );
  }

  get skipped_tests() {
    return Object.values(this.counts).reduce(
      (sum, count) => sum + count.skipped_tests,
      0,
    );
  }
}

export class ErroredCase {
 errored_cases(){

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

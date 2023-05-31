class Summary {
  constructor(implementations) {
    // console.log((implementations))

    this.implementations = implementations.sort((each, other) => {
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
    const counts = new Set(Object.values(this.counts).map(count => count.total_cases));
    // console.log(counts)
    if (counts.size !== 1) {
      const summary = Object.entries(this.counts)
        .map(([each, count]) => `  ${each.split('/').pop()}: ${count.total_cases}`)
        .join('\n');
      throw new InvalidBowtieReport(`Inconsistent number of cases run:\n\n${summary}`);
    }
    return counts.values().next().value;
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

export default Summary;

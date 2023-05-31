class Summary {
  constructor(implementations) {
    // console.log((implementations))

    this.implementations = implementations.sort((each, other) => {
      const key = `${each.language}${each.name}`;
      const otherKey = `${other.language}${other.name}`;
      return key < otherKey ? -1 : 1;
    });
    this.did_fail_fast = false;
  }
}

export default Summary;

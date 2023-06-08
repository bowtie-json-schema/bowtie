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

export default Summary;

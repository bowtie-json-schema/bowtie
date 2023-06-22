class Summary {
  constructor(lines) {
    this.lines = lines;
    try {
      const runInfoData = this.lines[0];
      const implementationsArray = Object.values(runInfoData.implementations);

      this.implementations = implementationsArray.sort((each, other) => {
        const key = `${each.language}${each.name}`;
        const otherKey = `${other.language}${other.name}`;
        return key < otherKey ? -1 : 1;
      });
      this.didFailFast = false;
    } catch (error) {
      console.log(error);
    }
  }
}

export default Summary;

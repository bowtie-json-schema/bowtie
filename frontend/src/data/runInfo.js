import Summary from "./summary";

export class RunInfo {
  constructor(lines) {
    this.lines = lines;
    const runInfoData = this.lines[0];
    this.started = runInfoData.started;
    this.bowtieVersion = runInfoData.bowtie_version;
    this.dialect = runInfoData.dialect;
    this.implementations = runInfoData.implementations;
    this.metadata = runInfoData.metadata;
  }

  createSummary() {
    return new Summary(this.lines);
  }
}

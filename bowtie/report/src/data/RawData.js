import { RunInfo } from "./run-Info";

function rawData(data) {
  let lines = data.map(line => JSON.parse(line));
  // console.log(lines)
  new RunInfo(lines[0]);
}

export default rawData;
import type { JestConfigWithTsJest } from "ts-jest";

const jestConfig: JestConfigWithTsJest = {
  transform: {
    "^.+\\.tsx?$": ["ts-jest", {}],
  },
};
export default jestConfig;

import { describe, expect, test } from "@jest/globals";
import Dialect, { DRAFT7 } from "./Dialect";

describe("Dialect", () => {
  test("Dialect.forPath", () => {
    expect(Dialect.forPath(DRAFT7.path)).toBe(DRAFT7);
  });
});

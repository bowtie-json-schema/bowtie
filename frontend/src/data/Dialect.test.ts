import { describe, expect, test } from "@jest/globals";
import Dialect from "./Dialect";

describe("Dialect", () => {
  test("Dialect.forPath", () => {
    const draft7 = Dialect.forPath("draft7");
    expect(draft7.firstPublicationDate).toStrictEqual(new Date("2017-11-19"));
  });
});

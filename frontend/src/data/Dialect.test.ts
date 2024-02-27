import { describe, expect, test } from "vitest";
import Dialect from "./Dialect";

const expectedDraft7 = {
  uri: "http://json-schema.org/draft-07/schema#",
  path: "draft7",
  prettyName: "Draft 7",
  firstPublicationDate: new Date("2017-11-19"),
};

describe("Dialect", () => {
  test("Dialect.forPath", () => {
    const draft7 = Dialect.forPath("draft7");
    expect(draft7.firstPublicationDate).toStrictEqual(new Date("2017-11-19"));
    expect(draft7).toEqual(expectedDraft7);
  });
});

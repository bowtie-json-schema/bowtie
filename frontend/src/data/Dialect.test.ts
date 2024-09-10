import { describe, expect, test } from "vitest";

import Dialect from "./Dialect";

describe("Dialect", () => {
  test("Dialect.withName", () => {
    expect(Dialect.withName("draft7")).toEqual({
      uri: "http://json-schema.org/draft-07/schema#",
      shortName: "draft7",
      prettyName: "Draft 7",
      firstPublicationDate: new Date("2017-11-19"),
      routePath: "/dialects/draft7",
      benchmarksRoutePath: "/benchmarks/draft7",
    });
  });
});

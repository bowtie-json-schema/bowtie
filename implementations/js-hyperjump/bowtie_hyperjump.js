import readline from "readline/promises";
import os from "os";
import process from "process";
import { addSchema, validate } from "@hyperjump/json-schema/draft-2020-12";
import "@hyperjump/json-schema/draft-2019-09";
import "@hyperjump/json-schema/draft-07";
import "@hyperjump/json-schema/draft-06";
import "@hyperjump/json-schema/draft-04";
import packageJson from "./node_modules/@hyperjump/json-schema/package.json" assert { type: "json" };

const hyperjump_version = packageJson.version;

const stdio = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

function send(data) {
  console.log(JSON.stringify(data));
}

var started = false;
var dialect = null;

// Skip
const keywordsNotInSchemaMessage =
  "Ignoring schema meta-data keywords in places that are not schemas (such as a $id in a const) is not supported. Because this implementation is dialect agnostic, there's no way to know whether a location is a schema or not. Especially because there's no reason for a schema to use keywords in places that aren't schemas, I'm not concerned about making it work.";
const keywordsNotInSchemaSkippedTests = [
  "id inside an enum is not a real identifier",
  "$id inside an enum is not a real identifier",
  "$id inside an unknown keyword is not a real identifier",
  "naive replacement of $ref with its destination is not correct",
  "$ref prevents a sibling id from changing the base uri",
  "$ref prevents a sibling $id from changing the base uri",
  "$anchor inside an enum is not a real identifier",
  "$anchor inside an enum is not a real identifier",
  "$id inside an unknown keyword is not a real identifier",
].reduce((acc, description) => {
  acc[description] = keywordsNotInSchemaMessage;
  return acc;
}, {});

const boundaryCrossingMessage =
  "JSON pointers that cross schema resource boundaries are not suppported. There might be a way to solve this, but because this functionality has been removed from the spec and there is no good reason to do this in any version of the spec, it will probably never be fixed.";
const boundaryCrossingSkippedTests = {
  "base URI change - change folder in subschema": boundaryCrossingMessage,
};

const modernSkippedTests = { ...keywordsNotInSchemaSkippedTests };
const legacySkippedTests = {
  ...boundaryCrossingSkippedTests,
  ...keywordsNotInSchemaSkippedTests,
};

const dialectSkippedTests = {
  "https://json-schema.org/draft/2020-12/schema": modernSkippedTests,
  "https://json-schema.org/draft/2019-09/schema": modernSkippedTests,
  "http://json-schema.org/draft-07/schema#": legacySkippedTests,
  "http://json-schema.org/draft-06/schema#": legacySkippedTests,
  "http://json-schema.org/draft-04/schema#": legacySkippedTests,
};

const cmds = {
  start: async (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {
      version: 1,
      implementation: {
        language: "javascript",
        name: "hyperjump-jsv",
        version: hyperjump_version,
        homepage: "https://json-schema.hyperjump.io/",
        issues: "https://github.com/hyperjump-io/json-schema/issues",
        source: "https://github.com/hyperjump-io/json-schema",

        dialects: [
          "https://json-schema.org/draft/2020-12/schema",
          "https://json-schema.org/draft/2019-09/schema",
          "http://json-schema.org/draft-07/schema#",
          "http://json-schema.org/draft-06/schema#",
          "http://json-schema.org/draft-04/schema#",
        ],
        os: os.platform(),
        os_version: os.release(),
        language_version: process.version,
      },
    };
  },

  dialect: async (args) => {
    console.assert(started, "Not started!");
    dialect = args.dialect;
    return { ok: true };
  },

  run: async (args) => {
    console.assert(started, "Not started!");

    const testCase = args.case;

    for (const id in testCase.registry) {
      try {
        addSchema(testCase.registry[id], id, dialect);
      } catch {}
    }

    let results;
    if (testCase.description in dialectSkippedTests[dialect]) {
      results = testCase.tests.map((_) => {
        return {
          skipped: true,
          message: dialectSkippedTests[dialect][testCase.description],
        };
      });
    } else {
      try {
        const idToken =
          dialect === "http://json-schema.org/draft-04/schema#" ? "id" : "$id";
        const host = testCase.schema?.[idToken]?.startsWith("file:")
          ? "file://"
          : "https://example.com";
        const fakeURI = `${host}/bowtie.sent.schema.${args.seq.toString()}.json`;
        addSchema(testCase.schema, fakeURI, dialect);
        const _validate = await validate(fakeURI);
        results = testCase.tests.map((test) => {
          try {
            const result = _validate(test.instance);
            return { valid: result.valid };
          } catch (error) {
            return { errored: true, context: { message: error.message } };
          }
        });
      } catch (error) {
        results = testCase.tests.map((_) => ({
          errored: true,
          context: { message: error.message },
        }));
      }
    }

    return { seq: args.seq, results: results };
  },

  stop: async (_) => {
    console.assert(started, "Not started!");
    process.exit(0);
  },
};

async function main() {
  for await (const line of stdio) {
    const request = JSON.parse(line);
    const response = await cmds[request.cmd](request);
    send(response);
  }
}

main();

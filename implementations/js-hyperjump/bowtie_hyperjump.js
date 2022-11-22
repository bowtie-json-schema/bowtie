const path = require("path");
const readline = require("readline/promises");

const hyperjump_version = require(path.join(
  path.dirname(path.dirname(require.resolve("@hyperjump/json-schema"))),
  "package.json",
)).version;

const JsonSchema = require("@hyperjump/json-schema");

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
const boundaryCrossingMessage =
  "JSON pointers that cross schema resource boundaries are not suppported. There might be a way to solve this, but because this functionality has been removed from the spec and there is no good reason to do this in any version of the spec, it will probably never be fixed.";
const keywordsNotInSchemaMessage =
  "Ignoring schema meta-data keywords in places that are not schemas (such as a $id in a const) is not supported. Because this implementation is dialect agnostic, there's no way to know whether a location is a schema or not. Especially because there's no reason for a schema to use keywords in places that aren't schemas, I'm not concerned about making it work.";
const skippedTests = {
  "base URI change - change folder in subschema": boundaryCrossingMessage,
  "id inside an enum is not a real identifier": keywordsNotInSchemaMessage,
  "$id inside an enum is not a real identifier": keywordsNotInSchemaMessage,
  "$id inside an unknown keyword is not a real identifier":
    keywordsNotInSchemaMessage,
  "naive replacement of $ref with its destination is not correct":
    keywordsNotInSchemaMessage,
  "$ref prevents a sibling id from changing the base uri":
    keywordsNotInSchemaMessage,
  "$ref prevents a sibling $id from changing the base uri":
    keywordsNotInSchemaMessage,
  "$anchor inside an enum is not a real identifier": keywordsNotInSchemaMessage,
  "$anchor inside an enum is not a real identifier": keywordsNotInSchemaMessage,
  "$id inside an unknown keyword is not a real identifier":
    keywordsNotInSchemaMessage,
};

const cmds = {
  start: async (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {
      ready: true,
      version: 1,
      implementation: {
        language: "javascript",
        name: "hyperjump-jsv",
        version: hyperjump_version,
        homepage: "https://json-schema.hyperjump.io/",
        issues: "https://github.com/hyperjump-io/json-schema-validator/issues",

        dialects: [
          "https://json-schema.org/draft/2020-12/schema",
          "https://json-schema.org/draft/2019-09/schema",
          "http://json-schema.org/draft-07/schema#",
          "http://json-schema.org/draft-06/schema#",
          "http://json-schema.org/draft-04/schema#",
        ],
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
        JsonSchema.add(testCase.registry[id], id, dialect);
      } catch {}
    }

    const fakeURI = "bowtie.sent.schema." + args.seq.toString() + ".json";
    JsonSchema.add(testCase.schema, fakeURI, dialect);
    const schema = await JsonSchema.get(fakeURI);

    const validate = await JsonSchema.validate(schema);
    const promises = testCase.tests.map((test) => {
      if (testCase.description in skippedTests) {
        return {
          skipped: true,
          message: skippedTests[testCase.description],
        };
      } else {
        return { valid: validate(test.instance).valid };
      }
    });
    const results = await Promise.all(promises);
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

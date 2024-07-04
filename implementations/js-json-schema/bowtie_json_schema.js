import os from "os";
import process from "process";
import readline from "readline/promises";

import { Validator } from "@cfworker/json-schema";
import packageJson from "./node_modules/@cfworker/json-schema/package.json" with { type: "json" };

const json_schema_version = packageJson.version;

const DRAFTS = {
  "https://json-schema.org/draft/2020-12/schema": "2020-12",
  "https://json-schema.org/draft/2019-09/schema": "2019-09",
  "http://json-schema.org/draft-07/schema#": "7",
  "http://json-schema.org/draft-04/schema#": "4",
};

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

const cmds = {
  start: async (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {
      version: 1,
      implementation: {
        language: "javascript",
        name: "cfworker-json-schema",
        version: json_schema_version,
        homepage:
          "https://github.com/cfworker/cfworker/blob/main/packages/json-schema/README.md",
        issues: "https://github.com/cfworker/cfworker/issues",
        source: "https://github.com/cfworker/cfworker",

        dialects: [
          "https://json-schema.org/draft/2020-12/schema",
          "https://json-schema.org/draft/2019-09/schema",
          "http://json-schema.org/draft-07/schema#",
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

    try {
      const validator = new Validator(testCase.schema, DRAFTS[dialect]);
      for (const id in testCase.registry) {
        validator.addSchema(testCase.registry[id], id);
      }

      const results = testCase.tests.map((test) => {
        try {
          const result = validator.validate(test.instance);
          return { valid: result.valid };
        } catch (error) {
          return {
            errored: true,
            context: {
              traceback: error.stack,
              message: error.message,
            },
          };
        }
      });

      return { seq: args.seq, results: results };
    } catch (error) {
      return {
        errored: true,
        seq: args.seq,
        context: {
          traceback: error.stack,
          message: error.message,
        },
      };
    }
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

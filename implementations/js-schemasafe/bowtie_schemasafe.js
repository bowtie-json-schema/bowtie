import os from "os";
import process from "process";
import readline from "readline/promises";

import { validator } from "@exodus/schemasafe";
import packageJson from "./node_modules/@exodus/schemasafe/package.json" with { type: "json" };

const schemasafe_version = packageJson.version;

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
        name: "schemasafe",
        version: schemasafe_version,
        homepage: "https://github.com/ExodusMovement/schemasafe",
        issues: "https://github.com/ExodusMovement/schemasafe/issues",
        source: "https://github.com/ExodusMovement/schemasafe",

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
    let validate;
    try {
      validate = validator(testCase.schema, {
        mode: "spec",
        schemas: testCase.registry || {},
        $schemaDefault: args.dialect,
      });
    } catch (error) {
      return {
        seq: args.seq,
        errored: true,
        context: {
          traceback: error.stack,
          message: error.message,
        },
      };
    }

    let results;
    try {
      results = testCase.tests.map((test) => {
        try {
          return { valid: validate(test.instance) };
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
    } catch (error) {
      results = testCase.tests.map((_) => ({
        errored: true,
        context: {
          traceback: error.stack,
          message: error.message,
        },
      }));
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

import readline from "readline/promises";
import os from "os";
import process from "process";
import { Validator } from "jsonschema";
import packageJson from "./node_modules/jsonschema/package.json" with { type: "json" };

import draft3 from "json-metaschema/draft-03-schema.json" with { type: "json" };
import draft4 from "json-metaschema/draft-04-schema.json" with { type: "json" };
import draft6 from "json-metaschema/draft-06-schema.json" with { type: "json" };
import draft7 from "json-metaschema/draft-07-schema.json" with { type: "json" };

const jsonschema_version = packageJson.version;

const stdio = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

function send(data) {
  console.log(JSON.stringify(data));
}

var started = false;

const cmds = {
  start: async (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {
      version: 1,
      implementation: {
        language: "javascript",
        name: "jsonschema",
        version: jsonschema_version,
        homepage: "https://github.com/tdegrunt/jsonschema",
        issues: "https://github.com/tdegrunt/jsonschema/issues",
        source: "https://github.com/tdegrunt/jsonschema",

        dialects: [
          "http://json-schema.org/draft-07/schema#",
          "http://json-schema.org/draft-06/schema#",
          "http://json-schema.org/draft-04/schema#",
          "http://json-schema.org/draft-03/schema#",
        ],
        os: os.platform(),
        os_version: os.release(),
        language_version: process.version,
      },
    };
  },

  dialect: async (_) => {
    console.assert(started, "Not started!");
    return { ok: false };
  },

  run: async (args) => {
    console.assert(started, "Not started!");

    const testCase = args.case;

    try {
      const validator = new Validator();

      validator.addSchema(draft3);
      validator.addSchema(draft4);
      validator.addSchema(draft6);
      validator.addSchema(draft7);

      for (const id in testCase.registry) {
        validator.addSchema(testCase.registry[id], id);
      }

      const results = testCase.tests.map((test) => {
        try {
          const result = validator.validate(test.instance, testCase.schema);
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

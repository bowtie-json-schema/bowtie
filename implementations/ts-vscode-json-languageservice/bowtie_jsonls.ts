import * as readline from "readline/promises";
import * as process from "process";

import {
  getLanguageService,
  SchemaDraft,
  TextDocument,
} from "vscode-json-languageservice";

const stdio = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

const schemaIds: { [id: string]: SchemaDraft } = {
  "https://json-schema.org/draft/2020-12/schema": SchemaDraft.v2020_12,
  "https://json-schema.org/draft/2019-09/schema": SchemaDraft.v2019_09,
  "http://json-schema.org/draft-07/schema#": SchemaDraft.v7,
  "http://json-schema.org/draft-06/schema#": SchemaDraft.v6,
  "http://json-schema.org/draft-04/schema#": SchemaDraft.v4,
  "http://json-schema.org/draft-03/schema#": SchemaDraft.v3,
};

function send(data) {
  console.log(JSON.stringify(data));
}

var started = false;
var dialect = null;
const ls = getLanguageService({});

const cmds = {
  start: async (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {
      ready: true,
      version: 1,
      implementation: {
        language: "typescript",
        name: "vscode-json-language-service",
        homepage: "https://github.com/microsoft/vscode-json-languageservice",
        issues:
          "https://github.com/microsoft/vscode-json-languageservice/issues",

        dialects: [
          "https://json-schema.org/draft/2020-12/schema",
          "https://json-schema.org/draft/2019-09/schema",
          "http://json-schema.org/draft-07/schema#",
          "http://json-schema.org/draft-06/schema#",
          "http://json-schema.org/draft-04/schema#",
          "http://json-schema.org/draft-03/schema#",
        ],
      },
    };
  },

  dialect: async (args) => {
    console.assert(started, "Not started!");
    dialect = schemaIds[args.dialect];
    return { ok: true };
  },

  run: async (args) => {
    console.assert(started, "Not started!");

    const testCase = args.case;

    for (const id in testCase.registry) {
    }

    let results;
    results = await Promise.all(
      testCase.tests.map(async (test) => {
        try {
          const textDoc = TextDocument.create(
            "example://bowtie-test.json",
            "json",
            0,
            JSON.stringify(test.instance),
          );
          const jsonDoc = ls.parseJSONDocument(textDoc);
          const semanticErrors = await ls.doValidation(
            textDoc,
            jsonDoc,
            { schemaDraft: dialect },
            testCase.schema,
          );
          return { valid: semanticErrors.length === 0 ? true : false };
        } catch (error) {
          return { errored: true, context: { message: error.message } };
        }
      }),
    );
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

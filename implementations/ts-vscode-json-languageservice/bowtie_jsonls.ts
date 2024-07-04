import * as readline from "readline/promises";
import * as process from "process";
import * as os from "os";
import * as packageJson from "./node_modules/vscode-json-languageservice/package.json";

const jsonls_version = packageJson.version;

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
      version: 1,
      implementation: {
        language: "typescript",
        name: "vscode-json-language-service",
        version: jsonls_version,
        homepage: "https://github.com/microsoft/vscode-json-languageservice",
        issues:
          "https://github.com/microsoft/vscode-json-languageservice/issues",
        source: "https://github.com/microsoft/vscode-json-languageservice",

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
          return {
            errored: true,
            context: {
              traceback: error.stack,
              message: error.message,
            },
          };
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

import os from "os";
import process from "process";
import readline from "readline/promises";

import Jedison from "jedison";
import packageJson from "./node_modules/jedison/package.json" with { type: "json" };

const stdio = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

function send(data) {
  console.log(JSON.stringify(data));
}

let started = false;
let dialect = null;

const dialects = [
  "https://json-schema.org/draft/2020-12/schema",
  "https://json-schema.org/draft/2019-09/schema",
  "http://json-schema.org/draft-07/schema#",
  "http://json-schema.org/draft-06/schema#",
  "http://json-schema.org/draft-04/schema#",
];

// Jedison does not support these keywords, nor validating against the
// metaschemas (which are built on them)
const unsupported = [
  /"\$dynamicRef"/,
  /"\$dynamicAnchor"/,
  /"\$recursiveRef"/,
  /"\$recursiveAnchor"/,
  /"\$ref":"https?:\/\/json-schema\.org\//,
];

function isSupported(schema, registry) {
  const source = JSON.stringify(schema);

  if (unsupported.some((pattern) => pattern.test(source))) {
    return false;
  }

  // Remote documents that use unsupported keywords, if the schema refers to them
  for (const [url, document] of Object.entries(registry)) {
    const remote = JSON.stringify(document);
    if (
      source.includes(url) &&
      unsupported.some((pattern) => pattern.test(remote))
    ) {
      return false;
    }
  }

  // A custom metaschema may change the vocabularies, which Jedison does not support
  const declared =
    schema !== null && typeof schema === "object" ? schema.$schema : undefined;
  const normalize = (uri) => uri.replace(/^https?:\/\//, "").replace(/#$/, "");
  return !(
    typeof declared === "string" &&
    !dialects.some((dialect) => normalize(dialect) === normalize(declared))
  );
}

function errorContext(error) {
  return { traceback: error.stack, message: error.message };
}

const cmds = {
  start: async (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {
      version: 1,
      implementation: {
        language: "javascript",
        name: "jedison",
        version: packageJson.version,
        homepage: "https://germanbisurgi.github.io/jedison-docs/",
        issues: "https://github.com/germanbisurgi/jedison/issues",
        source: "https://github.com/germanbisurgi/jedison",

        dialects,
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
    const registry = testCase.registry || {};

    if (!isSupported(testCase.schema, registry)) {
      return {
        seq: args.seq,
        results: testCase.tests.map(() => ({
          skipped: true,
          message:
            "$dynamicRef, $recursiveRef, metaschemas and custom vocabularies are not supported",
        })),
      };
    }

    const fetch = async (url) => {
      if (Object.hasOwn(registry, url)) {
        return { ok: true, json: async () => structuredClone(registry[url]) };
      }
      return { ok: false, status: 404, json: async () => ({}) };
    };

    let schema = structuredClone(testCase.schema);
    if (schema !== null && typeof schema === "object" && !schema.$schema) {
      schema.$schema = dialect;
    }

    let refParser;
    try {
      refParser = new Jedison.RefParser({ fetch });
      await refParser.dereference(schema);
    } catch (error) {
      return { seq: args.seq, errored: true, context: errorContext(error) };
    }

    const results = testCase.tests.map((test) => {
      let jedison;
      try {
        // The suite tests format both as an annotation and as an assertion
        const assertFormat = !test.description.includes(
          "only an annotation by default",
        );
        jedison = new Jedison.Create({ schema, refParser, assertFormat });
        jedison.setValue(structuredClone(test.instance));
        return { valid: jedison.getErrors().length === 0 };
      } catch (error) {
        return { errored: true, context: errorContext(error) };
      } finally {
        if (jedison) {
          jedison.destroy();
        }
      }
    });

    return { seq: args.seq, results };
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

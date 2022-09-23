const readline = require("readline");

const DRAFTS = {
  "https://json-schema.org/draft/2020-12/schema": require("ajv/dist/2020"),
  "https://json-schema.org/draft/2019-09/schema": require("ajv/dist/2019"),
  "http://json-schema.org/draft-07/schema#": require("ajv"),
  "http://json-schema.org/draft-04/schema#": require("ajv-draft-04"),
};
var ajv;

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
  start: (args) => {
    console.assert(args.version === 1, { args });
    started = true;
    return {
      ready: true,
      version: 1,
      implementation: {
        language: "javascript",
        name: "ajv",
        homepage: "https://ajv.js.org/",
        issues: "https://github.com/ajv-validator/ajv/issues",

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

  dialect: (args) => {
    console.assert(started, "Not started!");

    // For some reason ajv's process for Draft 6 is different, so split.
    if (args.dialect !== "http://json-schema.org/draft-06/schema#") {
      ajv = new DRAFTS[args.dialect]();
    } else {
      const Ajv = require("ajv");
      const draft6MetaSchema = require("ajv/dist/refs/json-schema-draft-06.json");

      ajv = new Ajv();
      ajv.addMetaSchema(draft6MetaSchema);
    }
    return { ok: true };
  },

  run: (args) => {
    console.assert(started, "Not started!");

    try {
      const testCase = args.case;
      const registry = testCase.registry;

      ajv.removeSchema(); // Clear the cache.
      for (const id in registry) ajv.addSchema(registry[id], id);

      const validate = ajv.compile(testCase.schema);

      return {
        seq: args.seq,
        results: testCase.tests.map((test) => ({
          valid: validate(test.instance),
        })),
      };
    } catch (e) {
      return {
        errored: true,
        seq: args.seq,
        context: { error: e.toString() },
      };
    }
  },

  stop: (_) => {
    console.assert(started, "Not started!");
    process.exit(0);
  },
};

stdio.on("line", (line) => {
  const request = JSON.parse(line);
  const response = cmds[request.cmd](request);
  send(response);
});

const readline = require("readline/promises");

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
    const schema = JsonSchema.get(fakeURI);

    const validate = await JsonSchema.validate(schema);
    const promises = testCase.tests.map((test) => ({
      valid: validate(test.instance).valid,
    }));
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
